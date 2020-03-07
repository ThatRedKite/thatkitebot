class evaluator:
    def __init__(self, message:str = ""):
        self.message = message
        self.output:str = ""
        self.count:int = 0
        self.cyrillic =["Б", "Г", "б", "в", "г",
                        "д", "Д", "Ж", "ж", "З",
                        "з", "И", "и", "Й", "й",
                        "К", "к", "Л", "л", "П",
                        "п", "Т", "т", "У", "у",
                        "Ф", "ф", "Х", "х", "Ц",
                        "ц", "Ч", "ч", "Ш", "ш",
                        "Щ", "щ", "Ъ", "ъ", "Ы",
                        "ы", "Ь", "ь", "Э", "э",
                        "Ю", "ю", "Я", "я", "Ё",
                        "ё", "к"]

    def evaluate(self, treshold):
        COUNTER = 0
        alphabet = self.cyrillic
        message = self.message
        try:
            for letter in message:
                if letter in alphabet:
                    COUNTER += 1
        except Exception as exc:
            return exc
        finally:
            try:
                if COUNTER > treshold: 
                    return False
                else:
                    return True
            except NameError as exc:
                return str(exc)
    
    def count(self):
        COUNTER = 0
        alphabet = self.cyrillic
        message = self.message
        try:
            for letter in message:
                if letter in alphabet:
                    COUNTER += 1
        except Exception as exc:
            print(exc)
        finally:
            return COUNTER
