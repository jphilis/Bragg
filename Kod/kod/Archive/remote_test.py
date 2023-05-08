from pexpect import spawn
import getpass

# Get the login details from the user
# username = input("Enter your username: ")
username = 'jakonil'
password = getpass.getpass("Enter your password: ")

# Connect to the remote server
child = spawn(f"ssh {username}@planck-o.fy.chalmers.se")

# Wait for the password prompt and send the password
child.expect("Password:")
child.sendline(password)

# Wait for the command prompt and print the output
child.expect("$")
print(child.before)
