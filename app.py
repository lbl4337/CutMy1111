from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
import uuid
from datetime import datetime
from config import Config
from database import db, Order, init_db

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化数据库
init_db(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def generate_order_id():
    """生成订单号"""
    date_str = datetime.now().strftime('%Y%m%d')
    random_num = str(uuid.uuid4().int)[:6]
    return f'ORD-{date_str}-{random_num}'


@app.route('/')
def index():
    """报价工具首页"""
    return render_template('index.html')


@app.route('/admin')
def admin():
    """订单管理后台"""
    return render_template('admin.html')


@app.route('/api/materials')
def get_materials():
    """获取材料列表"""
    return jsonify(app.config['MATERIALS'])


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传文件"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件上传'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400

    if file and allowed_file(file.filename):
        original_name = file.filename
        ext = original_name.rsplit('.', 1)[1].lower()
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        return jsonify({
            'success': True,
            'file_url': f'/uploads/{filename}',
            'file_name': filename,
            'file_original_name': original_name
        })

    return jsonify({'error': '不支持的文件类型'}), 400


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """提供上传文件的访问"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/submit-order', methods=['POST'])
def submit_order():
    """提交订单"""
    data = request.json

    # 验证必填字段
    if not data.get('client_name'):
        return jsonify({'error': '请填写客户姓名'}), 400

    if not data.get('items') or len(data['items']) == 0:
        return jsonify({'error': '请至少添加一块板材'}), 400

    # 计算总价
    total_price = calculate_total_price(data['items'], data.get('ship_cost', 18))

    # 生成订单号
    order_id = generate_order_id()

    # 保存订单
    order = Order(
        order_id=order_id,
        client_name=data['client_name'],
        client_contact=data.get('client_contact', ''),
        order_date=datetime.now().strftime('%Y-%m-%d'),
        shape='rect',  # 默认形状
        dims=json.dumps({}),  # 简化为空
        qty=sum(item.get('qty', 1) for item in data['items']),
        material=data['items'][0].get('material', 'birch15'),
        material_name=app.config['MATERIALS'].get(data['items'][0].get('material', 'birch15'), {}).get('name', ''),
        design_service=data.get('design_service', 'file'),
        design_note=data.get('design_note', ''),
        grain_direction=data.get('grain_direction', 'none'),
        file_url=data.get('file_url'),
        file_name=data.get('file_name'),
        file_original_name=data.get('file_original_name'),
        processing=json.dumps({
            'items': data['items'],
            'ship_cost': data.get('ship_cost', 18)
        }),
        estimated_price=str(total_price),
        status='pending'
    )

    try:
        db.session.add(order)
        db.session.commit()
        return jsonify({
            'success': True,
            'order_id': order_id,
            'estimated_price': total_price,
            'message': '订单提交成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def calculate_total_price(items, ship_cost=18):
    """计算总价"""
    total = 0
    for item in items:
        # 计算材料费
        material = app.config['MATERIALS'].get(item.get('material', 'birch15'), {})
        area = (item.get('length', 0) / 1000) * (item.get('width', 0) / 1000) * item.get('qty', 1)
        material_cost = material.get('price', 130) * area

        # 计算加工费
        process_cost = 0

        # 钻孔
        drill_count = item.get('drill', 0) * item.get('qty', 1)
        process_cost += drill_count * app.config['PROCESS_PRICES']['drill']

        # 圆角
        round_count = item.get('round', 0) * item.get('qty', 1)
        process_cost += round_count * app.config['PROCESS_PRICES']['round']

        # 封边
        if item.get('edge', False):
            perimeter = ((item.get('length', 0) + item.get('width', 0)) / 1000) * 2
            process_cost += perimeter * app.config['PROCESS_PRICES']['edge'] * item.get('qty', 1)

        # 砂光
        if item.get('sand'):
            sand_price = app.config['PROCESS_PRICES']['sand_double'] if item['sand'] == 'double' else \
            app.config['PROCESS_PRICES']['sand_single']
            process_cost += area * sand_price

        # 涂装
        if item.get('coat'):
            coat_price = app.config['PROCESS_PRICES']['coat_double'] if item['coat'] == 'double' else \
            app.config['PROCESS_PRICES']['coat_single']
            process_cost += area * coat_price

        total += material_cost + process_cost

    total += ship_cost
    return round(total, 2)


@app.route('/api/orders', methods=['GET'])
def get_orders():
    """获取订单列表"""
    status = request.args.get('status', 'all')
    limit = request.args.get('limit', 100, type=int)

    query = Order.query
    if status != 'all':
        query = query.filter(Order.status == status)

    orders = query.order_by(Order.created_at.desc()).limit(limit).all()
    return jsonify([order.to_dict() for order in orders])


@app.route('/api/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    """获取单个订单详情"""
    order = Order.query.filter_by(order_id=order_id).first()
    if not order:
        return jsonify({'error': '订单不存在'}), 404
    return jsonify(order.to_dict())


@app.route('/api/orders/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """更新订单状态"""
    data = request.json
    new_status = data.get('status')

    if new_status not in ['pending', 'paid', 'confirmed', 'completed']:
        return jsonify({'error': '无效的状态'}), 400

    order = Order.query.filter_by(order_id=order_id).first()
    if not order:
        return jsonify({'error': '订单不存在'}), 404

    order.status = new_status
    order.updated_at = datetime.utcnow()

    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/orders/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    """删除订单"""
    order = Order.query.filter_by(order_id=order_id).first()
    if not order:
        return jsonify({'error': '订单不存在'}), 404

    try:
        db.session.delete(order)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/calculate', methods=['POST'])
def calculate_price():
    """计算报价（不保存）"""
    data = request.json
    items = data.get('items', [])
    ship_cost = data.get('ship_cost', 18)

    total = calculate_total_price(items, ship_cost)

    # 计算明细
    details = []
    for idx, item in enumerate(items):
        material = app.config['MATERIALS'].get(item.get('material', 'birch15'), {})
        area = (item.get('length', 0) / 1000) * (item.get('width', 0) / 1000) * item.get('qty', 1)
        material_cost = material.get('price', 130) * area

        process_cost = 0
        process_details = []

        if item.get('drill', 0):
            cost = item['drill'] * item.get('qty', 1) * app.config['PROCESS_PRICES']['drill']
            process_cost += cost
            process_details.append({'name': '钻孔', 'cost': cost})

        if item.get('round', 0):
            cost = item['round'] * item.get('qty', 1) * app.config['PROCESS_PRICES']['round']
            process_cost += cost
            process_details.append({'name': '圆角', 'cost': cost})

        if item.get('edge', False):
            perimeter = ((item.get('length', 0) + item.get('width', 0)) / 1000) * 2
            cost = perimeter * app.config['PROCESS_PRICES']['edge'] * item.get('qty', 1)
            process_cost += cost
            process_details.append({'name': '封边', 'cost': round(cost, 2)})

        details.append({
            'index': idx + 1,
            'material_name': material.get('name'),
            'length': item.get('length'),
            'width': item.get('width'),
            'qty': item.get('qty'),
            'area': round(area, 4),
            'material_cost': round(material_cost, 2),
            'process_cost': round(process_cost, 2),
            'subtotal': round(material_cost + process_cost, 2),
            'process_details': process_details
        })

    return jsonify({
        'items': details,
        'ship_cost': ship_cost,
        'total': round(total, 2)
    })


if __name__ == '__main__':
    # 获取本机IP地址
    import socket

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    print('\n' + '=' * 50)
    print('  CutMy 报价系统已启动')
    print('=' * 50)
    print(f'  本地访问: http://127.0.0.1:5000')
    print(f'  局域网访问: http://{local_ip}:5000')
    print('=' * 50 + '\n')

    app.run(host='0.0.0.0', port=5000, debug=True)