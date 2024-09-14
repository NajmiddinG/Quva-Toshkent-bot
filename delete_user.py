import sqlite3

def delete_user(user_id):
    """Delete a user from the database."""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user = c.fetchone()
        if user:
            c.execute("DELETE FROM users WHERE user_id=?", (user_id,))
            conn.commit()
            print(f"User '{user_id}' has been deleted.")
            return f"{user_id} foydalanuvchi o'chirildi"
        else:
            print(f"User '{user_id}' not found in the database.")
            return f"{user_id} botga start bermagan!"
    except Exception as e:
        print(e)
        return "Xatolik yuz berdi"
    finally:
        conn.close()

# Example usage:
if __name__ == "__main__":
    # Prompt the user to enter an ID to delete
    user_id_to_delete = int(input("Enter the user ID to delete: "))
    print(delete_user(user_id_to_delete))
    
