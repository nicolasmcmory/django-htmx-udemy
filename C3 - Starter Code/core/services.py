from .models import Book, User


class BookService:
    # Return all books.
    @staticmethod
    def get_all():
        return Book.objects.all()

    # Return a book by its ID.
    @staticmethod
    def get_by_id(book_id):
        return Book.objects.get(pk=book_id)

    # Create and return a new book.
    @staticmethod
    def create(name, genres):
        return Book.objects.create(name=name, genres=genres)

    # Update and return an existing book.
    @staticmethod
    def update(book_id, name, genres):
        book = BookService.get_by_id(book_id)
        book.name = name
        book.genres = genres
        book.save()
        return book

    # Delete a book by its ID.
    @staticmethod
    def delete(book_id):
        return BookService.get_by_id(book_id).delete()


class UserService:
    # Store an existing user for user-specific operations.
    def __init__(self, user):
        self.user = user

    # Return all users.
    @staticmethod
    def get_all():
        return User.objects.all()

    # Return a user by their ID.
    @staticmethod
    def get_by_id(user_id):
        return User.objects.get(pk=user_id)

    # Return a user by their username.
    @staticmethod
    def get_by_username(username):
        return User.objects.get(username=username)

    # Create and return a user with a hashed password.
    @staticmethod
    def create(username, password, **extra_fields):
        return User.objects.create_user(
            username=username,
            password=password,
            **extra_fields,
        )

    # Delete a user by their ID.
    @staticmethod
    def delete(user_id):
        return UserService.get_by_id(user_id).delete()

    # Return all books belonging to this user.
    def get_books(self):
        return self.user.books.all()

    # Add a book to this user's collection.
    def add_book(self, book):
        self.user.books.add(book)
        return self.user

    # Remove a book from this user's collection.
    def remove_book(self, book):
        self.user.books.remove(book)
        return self.user
