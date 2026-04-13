from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50), unique=True, nullable=False)
    client_name = db.Column(db.String(100))
    client_contact = db.Column(db.String(100))
    order_date = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 产品信息
    shape = db.Column(db.String(20), default='rect')
    dims = db.Column(db.Text)  # JSON string
    qty = db.Column(db.Integer, default=1)
    material = db.Column(db.String(50))
    material_name = db.Column(db.String(100))

    # 设计服务
    design_service = db.Column(db.String(20), default='file')
    design_note = db.Column(db.Text)
    grain_direction = db.Column(db.String(20), default='none')

    # 文件
    file_url = db.Column(db.String(500))
    file_name = db.Column(db.String(200))
    file_original_name = db.Column(db.String(200))

    # 加工服务
    processing = db.Column(db.Text)  # JSON string

    # 价格和状态
    estimated_price = db.Column(db.String(20))
    status = db.Column(db.String(20), default='pending')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'client_name': self.client_name,
            'client_contact': self.client_contact,
            'order_date': self.order_date,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'shape': self.shape,
            'dims': json.loads(self.dims) if self.dims else {},
            'qty': self.qty,
            'material': self.material,
            'material_name': self.material_name,
            'design_service': self.design_service,
            'design_note': self.design_note,
            'grain_direction': self.grain_direction,
            'file_url': self.file_url,
            'file_name': self.file_name,
            'file_original_name': self.file_original_name,
            'processing': json.loads(self.processing) if self.processing else {},
            'estimated_price': self.estimated_price,
            'status': self.status,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print('数据库初始化完成')