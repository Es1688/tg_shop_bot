from .models import db
import json
from datetime import datetime

class UserCRUD:
    @staticmethod
    def get_or_create_user(user_id: int, username: str = None, 
                          first_name: str = None, last_name: str = None):
        with db.connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            )
            user = cursor.fetchone()
            
            if not user:
                cursor.execute(
                    """INSERT INTO users (id, username, first_name, last_name) 
                    VALUES (?, ?, ?, ?)""",
                    (user_id, username, first_name, last_name)
                )
                conn.commit()
                
                cursor.execute(
                    "SELECT * FROM users WHERE id = ?", (user_id,)
                )
                user = cursor.fetchone()
            
            return dict(user) if user else None
    
    @staticmethod
    def increment_orders_count(user_id: int):
        with db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET orders_count = orders_count + 1 WHERE id = ?",
                (user_id,)
            )
            conn.commit()

class OrderCRUD:
    @staticmethod
    def create_order(user_id: int, products: list, total_amount: float):
        with db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO orders (user_id, products, total_amount) 
                VALUES (?, ?, ?)""",
                (user_id, json.dumps(products), total_amount)
            )
            conn.commit()
            return cursor.lastrowid

class ChatHistoryCRUD:
    @staticmethod
    def add_message(user_id: int, role: str, message: str):
        with db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO chat_history (user_id, role, message) 
                VALUES (?, ?, ?)""",
                (user_id, role, message)
            )
            conn.commit()
    
    @staticmethod
    def get_recent_history(user_id: int, limit: int = 10):
        with db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT role, message FROM chat_history 
                WHERE user_id = ? 
                ORDER BY timestamp DESC LIMIT ?""",
                (user_id, limit)
            )
            return [dict(row) for row in cursor.fetchall()]
