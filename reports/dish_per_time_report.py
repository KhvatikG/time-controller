import os
import shutil
import subprocess
from datetime import datetime
import tempfile

import pandas as pd
import plotly.graph_objects as go
from aiogram.types import BufferedInputFile
from loguru import logger
from plotly.subplots import make_subplots

from tomato.core import settings
from utils import get_change_time_log_df

COLOR_SCHEME = {
    'Доставка': '#e74c3c',
    'Самовывоз': '#2ecc71',
    'dishes': '#9b59b6',
    'background': '#fdfefe',
    'grid': '#ebedef'
}


def fig_to_mp4(
        fig: go.Figure,
        frame_duration: float = 0.033,  # ~30 FPS
        final_pause: float = 15.0
) -> bytes:
    """Конвертирует Plotly Figure в MP4 с финальной паузой"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        frame_paths = []

        # 1. Генерация основных кадров анимации
        for i, frame in enumerate(fig.frames):
            frame_fig = go.Figure(fig.data, fig.layout)
            frame_fig.frames = [frame]
            frame_fig.update(data=frame.data)

            frame_path = os.path.join(tmp_dir, f"frame_{i:05d}.png")
            frame_fig.write_image(frame_path, engine="kaleido", width=1920, height=1080)
            frame_paths.append(frame_path)
            logger.debug(f"Generated main frame {i}")

        # 2. Добавление кадров паузы
        if frame_paths:
            last_frame = frame_paths[-1]
            pause_frames = int(final_pause / frame_duration)
            logger.info(f"Adding {pause_frames} pause frames")

            for i in range(pause_frames):
                new_frame_num = len(frame_paths)
                dst_path = os.path.join(tmp_dir, f"frame_{new_frame_num:05d}.png")
                shutil.copy(last_frame, dst_path)
                frame_paths.append(dst_path)
                logger.debug(f"Copied pause frame {i}")

        # 3. Проверка целостности кадров
        logger.info(f"Total frames generated: {len(frame_paths)}")
        for idx, path in enumerate(frame_paths):
            if not os.path.exists(path):
                raise FileNotFoundError(f"Missing frame {idx}: {path}")

        # 4. Создание видео с правильными параметрами
        output_path = os.path.join(tmp_dir, "animation.mp4")
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-framerate", str(int(1 / frame_duration)),
            "-i", os.path.join(tmp_dir, "frame_%05d.png"),  # Последовательная нумерация
            "-vf", "scale=1920:1080:flags=lanczos",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-t", str(len(frame_paths) * frame_duration),  # Точная длительность
            output_path
        ]

        logger.debug("FFmpeg command: " + " ".join(ffmpeg_cmd))
        subprocess.run(ffmpeg_cmd, check=True)
        logger.success("Video rendered successfully")

        with open(output_path, "rb") as f:
            return f.read()


def prepare_data(db_data_df: pd.DataFrame, api_data: dict, department_id: int, date_filter: datetime):
    """Обработка данных с фильтрацией по времени работы"""

    if not isinstance(department_id, int):
        raise ValueError(
            f"Неверный тип аргумента 'department_id': ожидается int, получен {type(department_id)}"
        )

    # Фильтрация и преобразование данных заказов
    waiting_time_df = db_data_df
    waiting_time_df['created_at'] = pd.to_datetime(waiting_time_df['created_at'])
    waiting_time_df = waiting_time_df[
        (waiting_time_df['department_id'] == str(department_id)) &
        (waiting_time_df['created_at'].dt.date == date_filter.date())
        ]

    # Фильтрация по времени работы заведения (10-22)
    waiting_time_df = waiting_time_df[
        (waiting_time_df['created_at'].dt.hour >= 10) &
        (waiting_time_df['created_at'].dt.hour <= 22)
        ]

    logger.info(f'Датафрэйм времени ожидания: для {department_id} на дату {date_filter.date()} \n{waiting_time_df}')
    # Агрегация по часам и типам заказов
    waiting_time_agg = waiting_time_df.groupby([
        waiting_time_df['created_at'].dt.hour.rename('hour'),
        'type_order'
    ]).agg(
        avg_wait=('time_minutes', 'mean')
    ).reset_index()
    logger.info(f'Датафрэйм времени ожидания после агрегации: \n{waiting_time_agg}')

    # Обработка данных продаж из API
    department_iiko_name = settings.SETTINGS.ORGANIZATION_ID_TO_IIKO_NAME.get(department_id)

    sales_data = [
        x for x in api_data['data']
        if x['Department'] == department_iiko_name
    ]

    sales_df = pd.DataFrame([{
        'hour': int(item['HourOpen']),
        'dishes_sold': item['DishAmountInt']
    } for item in sales_data])

    # Объединение данных
    if sales_df.empty or waiting_time_agg.empty:
        logger.warning(f"Нет данных для отдела {department_iiko_name}")
        return pd.DataFrame()

    merged_df = pd.merge(
        waiting_time_agg.pivot(index='hour', columns='type_order')['avg_wait'],
        sales_df,
        on='hour',
        how='outer',
    ).fillna(0)

    # Фильтрация финальных данных
    merged_df = merged_df[
        (merged_df['hour'] >= 10) &
        (merged_df['hour'] <= 22)
        ]

    return merged_df.sort_values('hour')


def create_combined_plot(data: pd.DataFrame, department_name: str):
    """Создание анимированного графика с улучшенной анимацией"""
    logger.info(f'Создание графика для {department_name}')
    if data.empty:
        logger.warning("Нет данных для построения графика")
        return

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Добавление трассировок
    for order_type in ['Доставка', 'Самовывоз']:
        if order_type in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=[],
                    y=[],
                    name=f'Время ({order_type})',
                    line=dict(color=COLOR_SCHEME[order_type], width=3, shape='spline'),
                    mode='lines+markers'
                ),
                secondary_y=False
            )

    if 'dishes_sold' in data.columns:
        fig.add_trace(
            go.Bar(
                x=[],
                y=[],
                name='Продажи',
                marker=dict(color=COLOR_SCHEME['dishes'], opacity=0.7),
                width=0.4
            ),
            secondary_y=True
        )

    # Параметры анимации
    steps_per_hour = 5
    frames = []
    hours = data['hour'].tolist()

    for i in range(len(hours)):
        hour = hours[i]
        for step in range(steps_per_hour):
            progress = (step + 1) / steps_per_hour

            # Данные для линий
            line_data = []
            for order_type in ['Доставка', 'Самовывоз']:
                if order_type in data.columns:
                    x = data['hour'][:i + 1].tolist()
                    y = data[order_type][:i + 1].tolist()

                    if i < len(hours) - 1 and step > 0:
                        x[-1] = hour + (hours[i + 1] - hour) * progress

                    line_data.append(
                        go.Scatter(
                            x=x,
                            y=y,
                            line=dict(shape='spline')
                        )
                    )

            # Данные для столбцов
            if 'dishes_sold' in data.columns:
                y_bar = [
                    *data['dishes_sold'][:i].tolist(),
                    data['dishes_sold'].iloc[i] * progress
                ]
                bar = go.Bar(
                    x=data['hour'][:i + 1].tolist(),
                    y=y_bar
                )
                line_data.append(bar)

            frames.append(go.Frame(data=line_data, name=f"frame_{i}_{step}"))

    fig.frames = frames
    fig.update_layout(
        title=dict(
            text=f"{department_name} - {datetime.now().strftime('%d.%m.%Y')}",
            font=dict(size=32, color='#2c3e50')
        ),
        margin=dict(l=10),
        xaxis=dict(
            title='Часы работы',
            tickmode='array',
            tickvals=data['hour'],
            range=[9.5, 22.5],  # Небольшие отступы для визуализации
            dtick=1,
            titlefont=dict(size=26),
            tickfont=dict(size=26),
        ),
        yaxis=dict(
            title='Среднее время (минуты)',
            titlefont=dict(color=COLOR_SCHEME['Доставка'], size=26),
            tickfont=dict(color=COLOR_SCHEME['Доставка'], size=24),
            gridcolor=COLOR_SCHEME['grid']
        ),
        yaxis2=dict(
            title='Количество блюд',
            titlefont=dict(color=COLOR_SCHEME['dishes'], size=26),
            tickfont=dict(color=COLOR_SCHEME['dishes'], size=24),
            overlaying='y',
            side='right'
        ),
        plot_bgcolor=COLOR_SCHEME['background'],
        hovermode='x unified',
        height=600,
        width=1000,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=24)
        ),
    )

    return fig


async def generate_report(department_name: str, api_data: dict, department_id: int):
    """Генерация и отправка отчета"""
    db_data_df = await get_change_time_log_df()
    # Подготовка данных
    df = prepare_data(db_data_df, api_data, department_id, datetime.now())

    # Создание графика
    fig = create_combined_plot(df, department_name)
    if fig is None:
        return

    # Экспорт в GIF
    gif_bytes = fig_to_mp4(fig)

    # Отправка в Telegram
    prepared_animation = BufferedInputFile(gif_bytes, filename='report.gif')

    return prepared_animation
