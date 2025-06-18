![CS50 Mail](./static/head.jpg)

### [Video Demo](https://youtu.be/0FZaUhoUUcw)

### Description: A Web application to send or receive email like Gmail or any other email based app or website. My website has a inbox, compose, sent page and function like to view whole email and repy is also there. You can simply login or register to use my web application. if you want to send an email then you can simply compose an email and write an email id of recipient to compose the email. if you want to sure about that your email is sent to recipient or not, you can simply login or register with the email id of recipient then you can see your mail that you sent recently. This is all the thing of my webite.

# Installation

- Clone / fork this repository.
- Create a virtual environment in your local Recifilter directory.
- Install the required libraries that are listed in [requirements.txt](/requirements.txt).

# Technologies

- Python
- Flask
- SQlite
- JQuery
- Javascript
- Html
- CSS
- Bootstrap 5

# Features

### Login/Register.

![login page](project/static/Login.png)
![register page](project/static/register.png)
It is simple register and login page where you can create or login to your Account to use me web application.
Users have to create an account prior to using this application. Validation is implemented in both front end and back end. Users have to provide a name (which will be used to greet users in the index page), a minimum of four-alphanumeric-characters username that will be used to identify which user has logged in, and a password. The password stored in the database is hashed first, but for safety measures, PLEASE DO NOT USE YOUR ACTUAL PASSWORD!


### Inbox.
![Inbox page](project/static/inbox.png)
It is a inbox page of my web application where all the email sent to you in your inbox by the sender. The content of Inbox is all the email that sent to you by the other users.

- sender: In the sender the email id of the sender who will send you or sent you.
- subject: In Subject, the subject of email the sender write in the email will show you.
- timing: In timing is obvious that it will show the timing of receiving the email by you.
- email: In email there is button for view email. It will show you whole information of email that is sender, recipient, subject, body etc.



### Compose.
![compose](project/static/compose.jpg)
It is a compose page of my web application where you can simply compose or write an email to the recipient and click on the send buttom to compose. In compose there is also lot element that i make for my web application.

- From: it is the element or a section of form of compose where the email id of sender. As you are composing this email than it obvious that the sender is you.
- To: it is the element or a section of form of compose where the email id of reccipient. Where you have to write the email id of the recipient you want to share.
- Subject: It is an element or a section of form of compose where the sender write the subject or a glance of your content of your email id you write for the recipient.

- body: It is an element of a section or form of compose where the sender write the main content of the email which the sender want to tell the recipient from his email.
- send: It is an element or a button of the compose page. it is the most important element this page. When you click the send button the email you write for the recipient will reach to him.

### View Email.
![view email](project/static/emails.jpg)
It is a button to see the all detail of the email you recieve or sent. You can simply click on the View email button in inbox and Sent page.  In view mail there is also lot element that i make for my web application.

- Sender: it is the element or a section of form of view email where the email id of sender who sent you the mail or the email sent to you from other users.
- To: it is the element or a section of form of view email where the information of recipient you email of you if you see the view mail of sent page.
- Subject: it is the element or a section of form of view mail where is the subject of email that you wrote or if you are viewing on sent page the subject you wrote will show.
- Timing: it is the element or a section of form. In timing is obvious that it will show the timing of receiving the email by you.
- Body: It is an element of a section or form where the sender write the main content of the email which the sender want to tell the recipient from his email. As same as in sent page.


### Reply.
![reply](project/static/reply.jpg)
It is a reply button to reply on the email that you have sent and receive.  In reply there is also lot element that i make for my web application.

- From: it is the element or a section of form of reply where the email id of sender. As you are replying this email than it obvious that the sender is you.
- To: it is the element or a section of form of reply where the email id of reccipient. Where you don't have to write the email id of the recipient because it been already written. It obvious you are replying.
- Subject:  It is an element or a section of form of reply where the sender write the subject or a glance of your content of your email id you write for the recipient.
- Body: It is an element of a section or form of reply where the sender write the main content of the email which the sender want to tell the recipient from his email.
- Reply: It is an element or a button of the reply page. it is the most important element this page. When you click the reply button the email you write for the recipient will reach to him.

### Sent.
![sent](project/static/sent.jpg)
It is a sent page of web application where you can see the all email sent by you to the recipient. You can also view the whole content of email to just click on View mail button and also reply.

- Recipient: In the recipient section of sent page, the email id of the recipient whom you will send or sent.
- Subject: In Subject, the subject of email the sender write in the email will show you.
- Timing:  it is the element or a section of form. In timing is obvious that it will show the timing of receiving the email by you.
- Email: In email there is button for view email. It will show you whole information of email that is sender, recipient, subject, body etc.

  That it! This is CS50X.