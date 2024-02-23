"""This file defines the API routes."""

# pylint: disable = no-name-in-module

from flask import Flask, Response, request, jsonify
from psycopg2.errors import ForeignKeyViolation

from database import get_db_connection

app = Flask(__name__)
conn = get_db_connection()


@app.route("/", methods=["GET"])
def index() -> Response:
    """Returns a welcome message."""
    return jsonify({
        "title": "Clown API",
        "description": "Welcome to the world's first clown-rating API."
    })


@app.route("/clown", methods=["GET", "POST"])
def get_clowns() -> Response:
    """Returns a list of clowns in response to a GET request;
    Creates a new clown in response to a POST request."""
    if request.method == "GET":
        order = request.args.get("order", "desc").lower()

        if order not in ["asc", "desc"]:
            return {"message": "Only use asc or desc"}, 400

        with conn.cursor() as cur:
            cur.execute(
                """SELECT c.clown_id, c.clown_name, c.speciality_id, AVG(r.rating) as average_rating, COUNT(r.rating) as num_ratings 
                FROM clown c
                LEFT JOIN review r on c.clown_id = r.clown_id
                GROUP BY c.clown_id
                ORDER BY average_rating """ + order + ";")

            clowns = []
            for row in cur.fetchall():
                clown = {
                    "clown_id": row["clown_id"],
                    "clown_name": row["clown_name"],
                    "speciality_id": row["speciality_id"],
                }
                if row["num_ratings"] is not None:
                    clown["num_ratings"] = row["num_ratings"]
                if row["average_rating"] is not None:
                    clown["average_rating"] = row["average_rating"]
                clowns.append(clown)

            return jsonify(clowns), 200
    else:
        data = request.json
        try:
            if "clown_name" not in data or "speciality_id" not in data:
                raise KeyError("New clowns need both a name and a speciality.")
            if not isinstance(data["speciality_id"], int):
                raise ValueError("Clown speciality must be an integer.")

            with conn.cursor() as cur:
                cur.execute("""INSERT INTO clown
                                 (clown_name, speciality_id)
                               VALUES (%s, %s)
                               RETURNING *;""",
                            (data["clown_name"], data["speciality_id"]))
                new_clown = cur.fetchone()
                conn.commit()
            return jsonify(new_clown), 201

        except (KeyError, ValueError, ForeignKeyViolation) as err:
            print(err.args[0])
            conn.rollback()
            return jsonify({
                "message": err.args[0]
            }), 400


@app.route("/clown/<int:id>", methods=["GET"])
def get_clown_by_id(id: int):
    """Returns all clown information based on the id given in the 
    route"""
    if request.method == "GET":
        with conn.cursor() as cur:
            cur.execute(
                """SELECT c.clown_id, c.clown_name, c.speciality_id, AVG(r.rating) as average_rating, COUNT(r.rating) as num_ratings 
                FROM clown c
                LEFT JOIN review r on c.clown_id = r.clown_id
                WHERE c.clown_id = %s
                GROUP BY c.clown_id;""", (id,))

            clown_id = cur.fetchone()

            if clown_id:
                clown = {
                    "clown_id": clown_id["clown_id"],
                    "clown_name": clown_id["clown_name"],
                    "speciality_id": clown_id["speciality_id"],
                }
                if clown_id["num_ratings"] is not None:
                    clown["num_ratings"] = clown_id["num_ratings"]
                if clown_id["average_rating"] is not None:
                    clown["average_rating"] = clown_id["average_rating"]

                return jsonify(clown), 200
            else:
                return jsonify({"error": True, "message": "Clown not found"}), 404


@app.route("/clown/<int:id>/review", methods=["POST"])
def clown_review(id: int):
    """Posts the ratings into the clown depending on
    the id that is given"""
    if request.method == "POST":
        data = request.json
        try:
            if "rating" not in data or data["rating"] not in range(1, 6):
                raise ValueError("Rating must be between 1-5")

            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO review
                    (clown_id, rating)
                    VALUES (%s, %s)
                    RETURNING *;""", (id, data["rating"])
                )
                conn.commit()
            return {"message": "Successfully added"}, 200

        except ValueError as err:
            conn.rollback()
            return {"message": err.args[0]}, 400


if __name__ == "__main__":
    app.run(port=8080, debug=True)
