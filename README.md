# Project 1

<b>Web Programming with Python and JavaScript</b>

For project1, I have made a book review website called Papyrus.

## Layout

I have made use of Bootstrap for the layout and design of the website, including containers and a navbar. Furthermore, I used a color palette that I found on <a href="https://www.color-hex.com/color-palette/9055">color-hex</a>.

## Files

My project folder includes a <i>static</i> folder containing a number images, an icon and a `styles.css` file. The <i>templates</i> folder contains 11 .html template files that make up the website. Furthermore, the project folder contains a `requirements.txt` file listing all the Python packages used, an `import.py` file that was used to import the books in `books.csv` into the database, a `helpers.py` file that defines the @login-required function and, lastly, an `application.py` file that contains all the necessary Flask code for running the website.

## Functionality

When a user browses to Papyrus for the first time, the user is asked to register an account. Without an account, a user cannot access the database or the API. After registration and subsequently logging in, the user is taken to the homepage with some general information about the website and a button that takes the user to the 'search' page.

On the 'search' page, the user has the ability to search for a book by typing in (part of) its title, its author or the book's ISBN number. If the user's search query does not match any of the books in the database, an error message will de displayed.

If the user's search query does match one or more books in the database, the user is shown a table with all the search results. By clicking on the title of the book, the user is taken to the 'book' page that contains more information about the book - including review data from Goodreads - as well as any reviews that other Papyrus users have written about the book. On the same page, the user is also able to leave a review himself/herself by choosing a rating between 1 and 5 and typing a more detailed opinion in the text-box. The user is only allowed to write one review per book. An error message will be displayed if the user tries to submit a second review.

If, however, the user clicks on the ISBN number of the book in the search results, the website will return a JSON response containing the book’s title, author, publication date, ISBN number, review count, and average score. The website's API can also be accessed by adding `/api/<isbn>` to the main URL, where `<isbn>` is the ISBN number of the book the user wants to get the data in JSON format for.

Lastly, under 'account settings' in the navbar, a user has the ability to change his/her password or delete his/her account. If a user decides to delete his/her account, his/her book reviews will also be deleted from the database.
