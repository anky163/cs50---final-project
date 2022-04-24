
# Grandma's mail box

#### Video Demo:  <https://youtu.be/AIiNfhjnfAY>

#### Description:
This is a web-based application allows an user to find, make friends with others and then they can send email to each other

The project contains:
1. register.html and login.html
    Where the user register an account then log in.

    Their username must be unique.

2. information.html
    Require user's informations like Name (required), Birthday, Place, Number and Email(required). The email must be unique.

    If they do not provide their Name or Email, the system will force them back to fulfill their (at least) required informations.

    The user can modify their informations here if they want to.

3. index.html
    Display all of user's informations

4. find.html
    Where the user can find all other users with their informations that they provide. The user can find a specific person by type in that person's Name, Email (These informations don't need to be precise).

    The user can send friend requests to them or:
        If the other already sent him/her a request, he/she can accept that request then they'll be in each other's friend list. Or he/she can reject that request, that'll delete that request

        If the user has already sent some of those others a request, the user can also cancel that request, that'll delete that request

        If the user and some of those others are already friends, he/she can unfriend them, that'll delete them from his/her friend list

5. request.html
    The user can also see all requests have been sent to them here, and they can accept or reject those requests

6. list.html
    This html shows all user's friends, or those the user's sent requests, or those've sent requests to the user.

    In case the person in friend list and the user are friends, the user can send email to them, or unfriend that person.

    In other cases, the user can accept/reject request, or cancel requests.

7. sending.html
    The user can only send mails to one of their already friends.
    
    Here the user provides Name and Email of their one particular friend, the mail's content and send it to that person.

    Or the user can go the their friend's list, seach for that person by their Name and Email. Once that person shows up, the user can press the "Send mail" button to redirect them to the sending email page and type in the mail's content then send it.

    The user can search in their sent history by provide Receiver's name (required), Receiver's email, and Date (These informations don't need to be precise)

8. inbox.html
    This page shows all user's inbox. The user can search some specific inboxes by type in the sender's Name and Email, date (These informations don't need to be precise).

    Each inbox there's an "Answer" button helps the user to answer that inbox.

9. change_password.html and "Delete Account" button:
    The user can change their password or even delete their account. If they want to delete their account, the system will ask them to confirm. Once they confirmed, all their informations in system's database will be deleted, included their mails.

10. app.py, helpers.py and mail.db
    These files contain backend's code and data.