from flask import Blueprint, render_template, request, jsonify
from flask_cors import CORS
from ..mongodb import db
from ..utils import login_required


db_api = Blueprint("database", __name__, url_prefix='/api/db')

@db_api.route('/test', methods=['GET'])
def get_movies():
    field = request.args.get('field', 'title')
    movies_collection = db.movies
    movies = movies_collection.find().limit(10)
    output = [{'title': movie.get(field, 'N/A')} for movie in movies]
    return jsonify(output)


@db_api.route("/database", methods=["GET"])
@login_required
def show_database():
    """
    Retrieve all documents from a specific collection.
    Adjust 'documents' below to match your collection name.
    """
    documents = list(db.instagram_dm.find())
    return render_template("database.html", documents=documents)


@db_api.route("/api/dms")
@login_required
def api_dms():
    page = int(request.args.get("page", 1))
    limit = 10
    skip = (page - 1) * limit

    total_count = db.instagram_dm.count_documents({})
    total_pages = (total_count + limit - 1) // limit

    cursor = (
        db.instagram_dm.find()
        .sort("timestamp", -1)
        .skip(skip)
        .limit(limit)
    )

    documents = list(cursor)
    for doc in documents:
        doc["_id"] = str(doc["_id"])  # convert ObjectId to string

    return jsonify({
        "documents": documents,
        "total_pages": total_pages
    })