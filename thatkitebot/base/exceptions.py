#  Copyright (c) 2019-2024 ThatRedKite and contributors

# this is a central place for all custom exceptions that don't fit anywhere else

class ImageTooLargeException(Exception):
    pass

class NoImageFoundException(Exception):
    pass


class InvalidTagsException(Exception):
    pass

class NoBookmarksException(Exception):
    pass

class NotEnoughMessagesException(Exception):
    pass

class StarboardDisabledException(Exception):
    pass
