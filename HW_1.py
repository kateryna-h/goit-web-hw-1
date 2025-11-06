from collections import UserDict
from datetime import datetime, date, timedelta
from abc import ABC, abstractmethod

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    def __init__(self, value):
        if not value.strip():
            raise ValueError("Name cannot be empty")
        super().__init__(value)

class Phone(Field):
    def __init__(self, value):
        if not self.phone_validation(value):
            raise ValueError("Invalid phone number")
        super().__init__(value)

    def phone_validation(self, value):
        return len(value) == 10 and value.isnumeric()
          
class Birthday(Field):
    def __init__(self, value):
        try:
            datetime.strptime(value, "%d.%m.%Y")  # перевірка формату
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(value)   # зберігаємо як рядок

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_birthday(self, birthday: str):
        self.birthday = Birthday(birthday)

    def add_phone(self, phone: str):
        self.phones.append(Phone(phone))
    
    def remove_phone(self, phone: str):
        phone_number = self.find_phone(phone)
        self.phones.remove(phone_number)
        
    def edit_phone(self, old_phone, new_phone):
        phone_number = self.find_phone(old_phone)
        if not phone_number:
            raise ValueError
        self.add_phone(new_phone)
        self.remove_phone(old_phone)

    def find_phone(self, phone: str):
        for i in self.phones:
            if i.value == phone:
                return i
        return None

    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(i.value for i in self.phones)}"

class AddressBook(UserDict):

    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name: str):
        return self.data.get(name)
        
    def delete(self, name):
        return self.data.pop(name, None)
    
    def __str__(self):
        return "\n".join(str(record) for record in self.data.values())
    
    def get_upcoming_birthdays(self):
        today = date.today()
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday:
                # Перетворюємо рядок у datetime.date
                birthday_date = datetime.strptime(record.birthday.value, "%d.%m.%Y").date()
                birthday_this_year = birthday_date.replace(year=today.year)

                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)

                delta = (birthday_this_year - today).days
                if 0 <= delta <= 7:
                    congratulation_date = birthday_this_year

                    if congratulation_date.weekday() == 5:  # субота
                        congratulation_date += timedelta(days=2)
                    elif congratulation_date.weekday() == 6:  # неділя
                        congratulation_date += timedelta(days=1)

                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "birthday": congratulation_date.strftime("%d.%m.%Y")
                    })

        return upcoming_birthdays

class BaseView(ABC):
    """Абстрактний базовий клас для різних інтерфейсів користувача."""

    @abstractmethod
    def show_message(self, message: str):
        pass

    @abstractmethod
    def show_contacts(self, contacts):
        pass

    @abstractmethod
    def show_help(self, commands: dict):
        pass


class ConsoleView(BaseView):
    """Консольна реалізація інтерфейсу користувача."""

    def show_message(self, message: str):
        print(message)

    def show_contacts(self, contacts):
        if not contacts:
            print("Контактів немає.")
        else:
            print("\n Список контактів:")
            for record in contacts.values():
                phones = ', '.join(p.value for p in record.phones)
                bday = record.birthday.value if record.birthday else "немає"
                print(f"{record.name.value}: {phones}; {bday}")
            print()

    def show_help(self, commands: dict):
        print("\n Доступні команди:")
        for cmd, desc in commands.items():
            print(f"{cmd:<20} — {desc}")
        print()        

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError as e:
            return "Contact is not found."
        except ValueError:
            return "Insufficient data"
        except IndexError:
            return "Enter a name of contact."
        except AttributeError:
            return "Contact not found."
    return inner

def parse_input(user_input):
    if not user_input.strip():
        return None, []
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args

@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone = args
    record = book.find(name)
    record.edit_phone(old_phone, new_phone)
    return f"Phone number for '{name}' updated."

@input_error
def get_phone(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    phones = "; ".join([p.value for p in record.phones])
    return f"{name}: {phones}"

def show_all(book: AddressBook):
    if not book.data:
        return "No contacts saved."
    return str(book)

@input_error
def add_birthday(args, book):
    name, birthday = args
    record = book.find(name)
    record.add_birthday(birthday)
    return "Birthday added"

@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        return record.birthday.value  # бо зберігаємо як рядок
    return "No birthday found"

@input_error
def birthdays(args, book):
    return book.get_upcoming_birthdays()

def main():
    book = AddressBook()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)
        if not command:
            print("Invalid command.")
            continue

        elif command in ["close", "exit"]:
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(get_phone(args, book))

        elif command == "all":
            print(book)

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")

main()
