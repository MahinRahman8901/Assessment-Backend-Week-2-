"""This file contains tests for the API."""

import json
from unittest.mock import patch
from app import app
from conftest import fake_clown, test_app


class TestAPIClownGet:
    """Contains tests for the /clown GET route"""

    @patch("app.conn")
    def test_get_clown_returns_200(self, mock_conn, test_app, fake_clown):
        """Tests that the /clown endpoint returns 200 on a GET request."""

        mock_conn.cursor.return_value\
            .__enter__.return_value\
            .fetchall.return_value = [fake_clown]

        res = test_app.get("/clown")

        assert res.status_code == 200

    @patch("app.conn")
    def test_get_clown_returns_list_of_dicts(self, mock_conn, test_app, fake_clown):
        """Tests that the /clown endpoint returns a list of valid dicts 
        on a GET request"""

        mock_conn.cursor.return_value\
            .__enter__.return_value\
            .fetchall.return_value = [fake_clown]

        res = test_app.get("/clown")
        data = res.json

        assert isinstance(data, list)
        assert all(isinstance(c, dict) for c in data)
        assert all("clown_id" in c
                   for c in data)

    @patch("app.conn")
    def test_get_clown_accesses_database(self, mock_conn, test_app):
        """Tests that the /clown endpoint makes expected calls to the database
        on a GET request."""

        mock_execute = mock_conn.cursor.return_value\
            .__enter__.return_value\
            .execute
        mock_fetch = mock_conn.cursor.return_value\
            .__enter__.return_value\
            .fetchall

        test_app.get("/clown")

        assert mock_execute.call_count == 1
        assert mock_fetch.call_count == 1


class TestAPIClownPost:
    """Contains tests for the /clown POST route"""

    @patch("app.conn")
    def test_post_clown_returns_201(self, mock_conn, test_app, fake_clown):
        """Tests that the /clown endpoint returns 201 on a POST request."""

        mock_conn.cursor.return_value\
            .__enter__.return_value\
            .fetchone.return_value = [fake_clown]

        res = test_app.post("/clown", json=fake_clown)

        assert res.status_code == 201

    @patch("app.conn")
    def test_post_clown_returns_400_on_invalid(self, mock_conn, test_app):
        """Tests that the /clown endpoint returns 400 on a POST request
        with an invalid body."""

        mock_conn.cursor.return_value\
            .__enter__.return_value\
            .fetchone.return_value = {}

        assert test_app.post("/clown", json={}).status_code == 400
        assert test_app.post("/clown", json={"clown_name": "A",
                                             "speciality_id": "r"}).status_code == 400

    @patch("app.conn")
    def test_post_clown_calls_db(self, mock_conn, test_app):
        """Tests that the /clown endpoint makes the expected calls to the db
        on a POST request."""

        mock_execute = mock_conn.cursor.return_value\
            .__enter__.return_value\
            .execute
        mock_fetch = mock_conn.cursor.return_value\
            .__enter__.return_value\
            .fetchone

        mock_fetch.return_value = {}

        _ = test_app.post("/clown", json={"clown_name": "Miriam",
                                          "speciality_id": 1})

        assert mock_fetch.call_count == 1
        assert mock_execute.call_count == 1


@patch('app.get_db_connection')
def test_get_clown_by_id(mock_get_db_connection, test_app, fake_clown):
    mock_cursor = mock_get_db_connection.return_value.cursor.return_value
    mock_cursor.fetchone.return_value = {
        "clown_id": fake_clown["clown_id"],
        "clown_name": fake_clown["clown_name"],
        "speciality_id": fake_clown["speciality_id"],
        "average_rating": 3.333,  # Assuming this value is derived from somewhere
        "num_ratings": 4
    }

    response = test_app.get('/clown/17')

    expected_data = {
        "clown_id": 17,
        "clown_name": "Bernice",
        "speciality_id": 3,
        "num_ratings": 4,
        "average_rating": 3.333,
    }

    assert response.status_code == 200
    assert response.get_json() == expected_data
