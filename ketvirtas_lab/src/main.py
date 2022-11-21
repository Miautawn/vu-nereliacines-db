import os
import json
from typing import List, Dict, Any

from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from neo4j_utils import Neo4jConnector

CONNECTION_URI = "bolt://localhost:7687"
CONNECTION_USER = "neo4j"
CONNECTION_PASSWORD = "password"

def _get_user(db, name: str, surname: str):
    query = f"MATCH (n:USER {{name:'{name}', surname: '{surname}'}}) return n"
    user = db.query(query)[0]["n"]
    return user

def _get_post(db, title: str):
    query = f"MATCH (n:POST {{title:'{title}'}}) return n"
    post = db.query(query)[0]["n"]
    return post
    
def _get_user_names(db):
    user_names = db.query("MATCH (n:USER) return n.name AS name, n.surname AS surname")
    return user_names

def _get_post_titles(db):
    posts = db.query("MATCH (n:POST) return n.title AS title")
    return posts

def _select_user_name(user_names: List[List[str]]):
    user_name_choices = [
        Choice(value=user_name, name=f"{user_name[0]} {user_name[1]}")
        for user_name in user_names
    ]
    user_name = inquirer.select(
        message="Select user name to query:", choices=user_name_choices
    ).execute()

    return user_name

def _select_post_title(post_titles: List[List[str]]):
    post_title_choices = [
        Choice(value=post_title)
        for post_title in post_titles
    ]
    post_title = inquirer.select(
        message="Select post title to query:", choices=post_title_choices
    ).execute()

    return post_title

def get_user_by_name(db):
    user_names = [list(user_dict.values()) for user_dict in _get_user_names(db)]
    user_name = _select_user_name(user_names)
    return _get_user(db, *user_name)

def get_post_by_title(db):
    post_titles = [title["title"] for title in _get_post_titles(db)]
    post_title = _select_post_title(post_titles)
    return _get_post(db, post_title)

def find_all_user_posts(db):
    user_names = [list(user_dict.values()) for user_dict in _get_user_names(db)]
    user_name = _select_user_name(user_names)

    query = f"MATCH (:USER {{name: '{user_name[0]}', surname: '{user_name[1]}'}}) -[:POSTED]-> (posts:POST) return posts"
    posts = [post["posts"] for post in db.query(query)]
    return posts

def find_all_people_who_liked_the_post(db):
    user_posts = find_all_user_posts(db)
    if user_posts:
        post_titles = [post["title"] for post in user_posts]
        post_title = _select_post_title(post_titles)
        
        query = f"MATCH (users:USER) -[:LIKES]-> (:POST {{title: '{post_title}'}}) return users"
        liked_users = [user["users"] for user in db.query(query)]
        return liked_users
    return []

def find_shortest_user_relation_by_friends(db):
    user_names = [list(user_dict.values()) for user_dict in _get_user_names(db)]

    print("Please select the first user:")
    user_name_1 = _select_user_name(user_names)
    user_names.remove(user_name_1)
    print("")
    print("Please select the second user:")
    user_name_2 = _select_user_name(user_names)
    print("")

    query = f"""
    MATCH (user_1:USER {{name: '{user_name_1[0]}', surname: "{user_name_1[1]}"}} ),
    (user_2:USER {{name: '{user_name_2[0]}', surname: "{user_name_2[1]}"}}),
    users = shortestPath((user_1)-[:FRIENDS*]-(user_2))
    RETURN users
    """

    linked_users = [
        user for user in db.query(query)[0]["users"] if isinstance(user, dict)
    ]
    return linked_users

def count_post_likes(db):
    post_titles = [title["title"] for title in _get_post_titles(db)]
    post_title = _select_post_title(post_titles)

    query = f"""
    MATCH (:POST {{title: '{post_title}'}}) <-[:LIKES]- (liking_user:USER)
    RETURN COUNT(liking_user) AS like_count
    """

    like_count = db.query(query)[0]["like_count"]
    return like_count

def main():
    db = Neo4jConnector(CONNECTION_URI, CONNECTION_USER, CONNECTION_PASSWORD)

    print("\nWelcome to the Fishermen Social Media!")
    while True:
        action = inquirer.select(
            message="Select an action:",
            choices=[
                Choice(value=0, name="Get user by name"),
                Choice(value=1, name="Get post by title"),
                Choice(value=2, name="Find all user posts"),
                Choice(value=3, name="Find users who liked a post"),
                Choice(value=4, name="Find the shortest friend relation chain between 2 users"),
                Choice(value=5, name="Count all the likes of the post")
            ],
        ).execute()

        print("\n" + "-" * 40)
        if(action == 0):
            user = get_user_by_name(db)
            print(f"{'NAME':<20}{'SURNAME':<20}{'AGE':<20}")
            print(f"{user['name']:<20}{user['surname']:<20}{user['age']:<20}")

        if(action == 1):
            post = get_post_by_title(db)
            print(f"{'TITLE':<30}{'DESCRIPTION':<30}")
            print(f"{post['title']:<30}{post['description']:<30}")

        if(action == 2):
            posts = find_all_user_posts(db)
            print(f"{'UUID':<20}{'TITLE':<30}{'DESCRIPTION':<30}")
            for post in posts:
                print(f"{post['UUID']:<20}{post['title']:<30}{post['description']:<30}")

        if(action == 3):
            liked_users = find_all_people_who_liked_the_post(db)
            print(f"{'NAME':<20}{'SURNAME':<20}{'AGE':<20}")
            for user in liked_users:
                print(f"{user['name']:<20}{user['surname']:<20}{user['age']:<20}")

        if(action == 4):
            linked_users = find_shortest_user_relation_by_friends(db)
            print("The shortest friend chain between these users are:")
            print(f"{'NAME':<20}{'SURNAME':<20}{'AGE':<20}")
            for user in linked_users:
                print(f"{user['name']:<20}{user['surname']:<20}{user['age']:<20}")

        if(action == 5):
            like_count = count_post_likes(db)
            print(f"This post is liked by {like_count} users!")

        proceed = inquirer.confirm(
            message="Would you like to query something else?",
        ).execute()
        if not proceed:
            break
        os.system("clear")


if __name__ == "__main__":
    main()
