from flask import request, jsonify, g
from .seller_view import login_required
from flask_request_validator import Param, PATH, validate_params
from exceptions import NoAffectedRowException, NoDataException


def product_endpoints(app, services, get_session):
    product_service = services.product_service

    @app.route("/product/register", methods=['GET', 'POST'])
    @login_required
    def register_product():
        if request.method == 'GET':
            # 상품 등록하기 페이지 들어갔을 때 1차 카테고리, 색상, 사이즈 불러오기
            session = None
            try:
                session = get_session()
                data_list = product_service.get_category_color_size(session)

                return jsonify(data_list), 200

            except Exception as e:
                session.rollback()
                return jsonify({'message': '{}'.format(e)}), 500

            finally:
                if session:
                    session.close()

        if request.method == 'POST':
            # 상품 등록하기
            session = None
            try:
                session = get_session()
                product_data = request.json
                product_data['seller_id'] = g.seller_id

                # 입력되야 하는 필수값들이 안들어왔을 때 에러 발생
                if product_data['sub_categories_id'] is None or product_data['name'] is None or \
                        product_data['main_image'] is None or product_data['is_sell'] is None or \
                        product_data['is_display'] is None or product_data['is_discount'] is None or \
                        product_data['price'] is None or product_data['detail'] is None or \
                        product_data['maximum_sell_count'] is None or product_data['minimum_sell_count'] is None:
                    return jsonify({'message': 'invalid request'}), 400

                if product_data['options'] is None:
                    return jsonify({'message': 'options not exist'}), 400

                # 옵션 안의 리스트의 키값들이 None 일 때 에러 발생
                for options in product_data['options']:
                    if options['color_id'] is None or options['size_id'] is None or options['is_inventory_manage'] is None:
                        return jsonify({'message': 'option data not exist'}), 400

                product_service.post_register_product(product_data, session)

                session.commit()
                return jsonify({'message': 'success'}), 200

            except KeyError:
                return jsonify({'message': 'key error'}), 400

            except NoAffectedRowException as e:
                session.rollback()
                return jsonify({'message': 'no affected row error {}'.format(e.message)}), e.status_code

            except Exception as e:
                session.rollback()
                return jsonify({'message': '{}'.format(e)}), 500

            finally:
                if session:
                    session.close()

    @app.route("/category/<int:category_id>", methods=['GET'])
    @login_required
    def get_sub_category_list(category_id):
        # 1차 카테고리 선택했을 때 2차 카테고리 리스트 불러오기
        session = None
        try:
            session = get_session()
            category_list = product_service.get_sub_categories(category_id, session)

            return category_list

        except Exception as e:
            session.rollback()
            return jsonify({'message': '{}'.format(e)}), 500

        finally:
            if session:
                session.close()

    @app.route("/product/update/<int:product_id>", methods=['GET', 'PUT'])
    @login_required
    @validate_params(
        Param('product_id', PATH, int)
    )
    def update_product(product_id):
        if request.method == 'GET':
            # 상품상세페이지(수정) 상품 데이터 가져오기
            session = None
            try:
                session = get_session()

                product_data = product_service.get_product(product_id, session)

                return jsonify(product_data)

            except NoDataException as e:
                session.rollback()
                return jsonify({'message': 'no data {}'.format(e)}), e.status_code

            except Exception as e:
                session.rollback()
                return jsonify({'message': '{}'.format(e)}), 500

            finally:
                if session:
                    session.close()

        if request.method == 'PUT':
            # 상품상세페이지(수정) 상품 데이터 업데이트하기
            session = None
            try:
                session = get_session()
                product_data = request.json
                product_data['product_id'] = product_id

                # 상품 데이터의 필수값이 들어오지 않았으면 에러 발생
                if product_data['sub_categories_id'] is None or product_data['name'] is None \
                        or product_data['is_sell'] is None or product_data['is_display'] is None \
                        or product_data['is_discount'] is None or product_data['price'] is None \
                        or product_data['main_image'] is None or product_data['detail'] is None \
                        or product_data['minimum_sell_count'] is None or product_data['maximum_sell_count'] is None:
                    return jsonify({'message': 'invalid request'}), 400

                # 상품데이터의 옵션값이 None 이면 에러 발생
                if product_data['options'] is None:
                    return jsonify({'message': 'options not exist'}), 400

                # 옵션 안의 키값들이 None 이면 에러 발생
                for options in product_data['options']:
                    if options['color_id'] is None or options['size_id'] is None \
                            or options['is_inventory_manage'] is None:
                        return jsonify({'message': 'option data not exist'}), 400

                product_data['seller_id'] = g.seller_id
                product_service.post_update_product(product_data, session)

                session.commit()
                return jsonify({'message': 'success'}), 200

            except NoAffectedRowException as e:
                session.rollback()
                return jsonify({'message': 'no affected row error {}'.format(e.message)}), e.status_code

            except Exception as e:
                session.rollback()
                return jsonify({'message': '{}'.format(e)}), 500

            finally:
                if session:
                    session.close()

    @app.route("/product/management", methods=['GET'])
    @login_required
    def management_product():
        # 셀러 상품 관리 페이지 들어갔을 때 등록된 셀러 상품들 가져오기
        session = None
        try:
            session = get_session()
            # 쿼리 스트링 가져오기
            limit = request.args.get('limit', None)
            offset = request.args.get('offset', None)
            is_sell = request.args.get('is_sell', None)
            is_discount = request.args.get('is_discount', None)
            is_display = request.args.get('is_display', None)
            name = request.args.get('name', None)
            code_number = request.args.get('code_number', None)
            product_number = request.args.get('product_id', None)
            start_date = request.args.get('start_date', None)
            end_date = request.args.get('end_date', None)
            seller_property_id = request.args.get('seller_property_id', None)
            brand_name_korean = request.args.get('brand_name_korean', None)

            # 쿼리스트링을 리스트로 만듬
            query_string_list = {
                'limit':                10 if limit is None else int(limit),
                'offset':               0 if offset is None else int(offset),
                'is_sell':              is_sell,
                'is_discount':          is_discount,
                'is_display':           is_display,
                'name':                 name,
                'code_number':          code_number,
                'product_number':       product_number,
                'start_date':           start_date,
                'end_date':             end_date,
                'seller_id':            g.seller_id,
                'brand_name_korean':    brand_name_korean,
                'seller_property_id':   seller_property_id
            }

            product_list = product_service.get_product_list(query_string_list, session)

            return jsonify(product_list)

        except Exception as e:
            session.rollback()
            return jsonify({'message': '{}'.format(e)}), 500

        finally:
            if session:
                session.close()
