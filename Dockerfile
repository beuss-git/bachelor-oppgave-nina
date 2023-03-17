FROM python:3.10

# https://stackoverflow.com/questions/68036484/qt6-qt-qpa-plugin-could-not-load-the-qt-platform-plugin-xcb-in-even-thou#comment133288708_68058308
RUN --mount=type=cache,sharing=locked,target=/var/cache/apt \
    --mount=type=cache,sharing=locked,target=/var/lib/apt \
    rm /etc/apt/apt.conf.d/docker-clean && \
    apt-get update && \
    apt-get install -qy --no-install-recommends \
        libgl1 libxkbcommon0 libegl1 libdbus-1-3 \
        libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxkbcommon-x11-0

WORKDIR /app

RUN python3 -m pip install poetry && \
    poetry config virtualenvs.in-project true

COPY pyproject.toml poetry.lock ./
RUN --mount=type=cache,sharing=locked,target=/root/.cache/pypoetry \
    poetry install --no-root

COPY app app
CMD ["poetry", "run", "python", "-c", "from app import main; main.main()"]
