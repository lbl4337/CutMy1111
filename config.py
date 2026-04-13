import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'cutmy-secret-key-2024')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///cutmy.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file
    ALLOWED_EXTENSIONS = {'dxf', 'dwg', 'pdf', 'png', 'jpg', 'jpeg', 'ai', 'cdr'}

    # 定价配置
    MATERIALS = {
        'birch9': {'name': '桦木多层板 9mm', 'price': 85, 'group': '桦木多层板'},
        'birch12': {'name': '桦木多层板 12mm', 'price': 110, 'group': '桦木多层板'},
        'birch15': {'name': '桦木多层板 15mm', 'price': 130, 'group': '桦木多层板'},
        'birch18': {'name': '桦木多层板 18mm', 'price': 145, 'group': '桦木多层板'},
        'marine12': {'name': '海洋板 12mm', 'price': 130, 'group': '海洋板'},
        'marine15': {'name': '海洋板 15mm', 'price': 150, 'group': '海洋板'},
        'marine18': {'name': '海洋板 18mm', 'price': 170, 'group': '海洋板'},
        'laminate9': {'name': '免漆板 9mm', 'price': 85, 'group': '免漆家具板', 'edge_price': 10},
        'laminate18': {'name': '免漆板 18mm', 'price': 130, 'group': '免漆家具板', 'edge_price': 10}
    }

    # 加工服务定价
    PROCESS_PRICES = {
        'drill': 3,  # 元/孔
        'round': 5,  # 元/角
        'sand_single': 10,  # 元/㎡
        'sand_double': 14,  # 元/㎡
        'edge': 10,  # 元/米
        'coat_single': 50,  # 元/㎡
        'coat_double': 100,  # 元/㎡
        'bevel': 6  # 元/米
    }