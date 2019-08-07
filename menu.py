from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_setup import Bar, Base, MenuItem, User

engine = create_engine('sqlite:///barmenu.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Joe Cool ", email="jcool@me.com",
             picture='https://bit.ly/2ZHVb2a')
session.add(User1)
session.commit()

# Menu for UrbanBurger
bar1 = Bar(user_id=1, name="Urban Burger")

session.add(bar1)
session.commit()

menuItem2 = MenuItem(user_id=1, name="beyond Burger", description="mimi yummy",
                     price="$7.50", course="Entree", bar=bar1)

session.add(menuItem2)
session.commit()


menuItem1 = MenuItem(user_id=1, name="Fries", description="with garlic and parmesan",
                     price="$2.99", course="Appetizer", bar=bar1)

session.add(menuItem1)
session.commit()

menuItem2 = MenuItem(user_id=1, name="Chicken Burger", description="fat abd chicken",
                     price="$5.50", course="Entree", bar=bar1)

session.add(menuItem2)
session.commit()

menuItem3 = MenuItem(user_id=1, name="Chocolate Cake", description=" served with ice cream",
                     price="$3.99", course="Dessert", bar=bar1)

session.add(menuItem3)
session.commit()

menuItem4 = MenuItem(user_id=1, name="Sirloin Burger", description="Meat baby",
                     price="$7.99", course="Entree", bar=bar1)

session.add(menuItem4)
session.commit()

menuItem5 = MenuItem(user_id=1, name="Root Beer", description="Best goodness",
                     price="$1.99", course="Beverage", bar=bar1)


# Menu for Super Stir Fry
bar2 = Bar(user_id=1, name="Super Stir Fry")

session.add(bar2)
session.commit()


menuItem1 = MenuItem(user_id=1, name="Chicken Stir Fry", description="yummy",
                     price="$7.99", course="Entree", bar=bar2)

session.add(menuItem1)
session.commit()

menuItem2 = MenuItem(user_id=1, name="Duck Duck",
                     description=" yummy", price="$25", course="Entree", bar=bar2)

session.add(menuItem2)
session.commit()

menuItem3 = MenuItem(user_id=1, name="Tuna Poke", description="Seared rare ahi, avocado, edamame, cucumber with wasabi soy sauce ",
                     price="15", course="Entree", bar=bar2)

session.add(menuItem3)
session.commit()

menuItem4 = MenuItem(user_id=1, name=" Guyoza ", description="Steamed dumplings made with vegetables, spices and meat. ",
                     price="12", course="Entree", bar=bar2)

session.add(menuItem4)
session.commit()

menuItem5 = MenuItem(user_id=1, name="Beef Noodle Soup", description="A Chinese noodle soup made of stewed or red braised beef, beef broth, vegetables and Chinese noodles.",
                     price="14", course="Entree", bar=bar2)

session.commit()


print ("added menu items!")
