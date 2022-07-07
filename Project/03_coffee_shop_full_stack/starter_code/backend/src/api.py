
from werkzeug import Response
import json
from flask_cors import CORS
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)

# CORS(app, resources={r"*/api/*": {"origins": '[http://localhost:8100]'}})
CORS(app)
# CORS Headers


@app.after_request
def after_request(response):
    response.headers.add(
        "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
    )
    response.headers.add(
        "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
    )
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


'''
@DONE uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES
'''
@DONE implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks')
def show_short_drinks():
    drinks_list = Drink.query.all()
    if drinks_list is None:
        abort(404)
    drinks = [drink.short() for drink in drinks_list]
    print(*drinks)
    return jsonify(
        {
            "success": True,
            "drinks": drinks
        }
    )


'''
@DONE implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def show_details(jwt):
    print(jwt)
    drinks_list = Drink.query.all()
    if drinks_list is None:
        abort(404)
    drinks = [drink.long() for drink in drinks_list]
    return jsonify(
        {
            "success": True,
            "drinks": drinks
        }
    )


'''
@DONE implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drinks(jwt):
    print(jwt)
    drink_body = request.get_json()
    if drink_body is None:
        abort(400)
    title = drink_body.get('title')
    recipe = drink_body.get('recipe')
    drink_exist = Drink.query.filter_by(title=title).first()
    if drink_exist is not None:
        abort(422)

    print(json.dumps(recipe))
    drink = Drink(
        title=title,
        recipe=json.dumps(recipe)
    )
    drink.insert()

    return jsonify(
        {
            "success": True,
            "drinks": drink.long(),
        })


'''
@DONE implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth(permission='patch:drinks')
def update_drinks(jwt, drink_id):
    print(jwt)

    drink = Drink.query.get(drink_id)
    drink_body = request.get_json()

    if drink is None:
        abort(404)

    if drink_body is None:
        abort(400)

    if "title" not in drink_body and "recipe" not in drink_body:
        abort(422)

    if "title" in drink_body:
        title = drink_body.get('title')
        drink.title = title

    if "recipe" in drink_body:
        recipe = drink_body.get('recipe')
        drink.recipe = json.dumps(recipe)

    drink.update()

    return jsonify(
        {
            "success": True,
            "drinks": drink.long(),
        })


'''
@DONE implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth(permission='delete:drinks')
def delete_drinks(jwt, drink_id):
    print(jwt)
    drink = Drink.query.get(drink_id)
    if drink is None:
        abort(404)
    drink.delete()

    return jsonify(
        {
            "success": True,
            "delete": drink.id,
        })


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@DONE implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''


@app.errorhandler(404)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": error.name
    }), 404


'''
@DONE implement error handler for 404
    error handler should conform to general task above
'''


@app.errorhandler(400)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": error.name
    }), 400


'''
@DONE implement error handler for AuthError
    error handler should conform to general task above
'''


@app.errorhandler(AuthError)
def handle_auth_error(ex: AuthError) -> Response:
    """
    serializes the given AuthError as json and sets the response status code accordingly.
    :param ex: an auth error
    :return: json serialized ex response
    """
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response
