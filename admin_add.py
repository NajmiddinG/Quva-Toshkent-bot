import sqlite3
ALLOWED_USER_IDS = {1157747787, 5294055251, 1456151744}

def add_admin(user_id, role='Admin'):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user = c.fetchone()
        if user:
            user_id = user[0]
            c.execute("UPDATE users SET user_type=? WHERE user_id=?", (role, user_id))
            conn.commit()
            print(f"""Role '{role}' added to user '{user_id}'.""")
            return f"""{user_id} muavvaffaqiyatli {role} ga aylandi"""
        else:
            print(f"""User '{user_id}' not found in the database.""")
            return f"""{user_id} botga start bermagan!"""
    except Exception as e:
        print(e)
        return f"""Xatolik yuz berdi"""

# Example usage:
if __name__ == "__main__":
    # Prompt the user to enter the admin user ID
    admin_id = int(input("Enter the admin user ID: "))
    
    # Add the admin user ID to the database
    add_admin(admin_id)
