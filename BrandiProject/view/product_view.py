from flask        import request, jsonify, g
from .seller_view import login_required

def product_endpoints(app, services):
    product_service = services.product_service

    @app.route("/product/register", methods=['POST'])
    @login_required
    def register_product():
        product_data              = request.json
        product_data['seller_id'] = g.seller_id
        product                   = product_service.post_register_product(product_data)

        if product == 'invalid request': return jsonify({'message':'INVALID_REQUEST'}), 400

        return jsonify({'message':'SUCCESS'}), 200
    
    @app.route("/product/update", methods=['POST'])
    @login_required
    def update_product():
        product_data              = request.json
        product_data['seller_id'] = g.seller_id
        product                   = product_service.post_update_product(product_data)

        if product == 'invalid request': return jsonify({'message':'INVALID_REQUEST'}), 400

        return jsonify({'message':'SUCCESS'}), 200

    @app.route("/product/management", methods=['GET'])
    @login_required
    def management_product():
        limit          = request.args.get('limit', None)
        offset         = request.args.get('offset', None)
        view           = request.args.get('view', None)
        is_sell        = request.args.get('is_sell', None)
        is_discount    = request.args.get('is_discount', None)
        is_display     = request.args.get('is_display', None)
        name           = request.args.get('name', None)
        code_number    = request.args.get('code', None)
        product_number = request.args.get('number', None)

        product_list = product_service.get_product_list(g.seller_id)

        product_list = [product for product in product_list if product['is_sell']==int(is_sell)] if is_sell is not None else product_list
        product_list = [product for product in product_list if product['is_discount']==int(is_discount)] if is_discount is not None else product_list
        product_list = [product for product in product_list if product['is_display']==int(is_display)] if is_display is not None else product_list
        product_list = [product for product in product_list if product['name']==name] if name is not None else product_list
        product_list = [product for product in product_list if product['code_number']==code_number] if code_number is not None else product_list
        product_list = [product for product in product_list if product['product_number']==product_number] if product_number is not None else product_list

        total = len(product_list)
        offset = 0 if offset is None else offset
        limit = 10 if limit is None else limit 
        product_list = product_list[int(offset):int(offset+limit)] if (offset and limit) is not None else product_list
        
        return jsonify({'product_list':product_list, 'total':total})