from . import db
from sqlalchemy.sql import func
from sqlalchemy import Column, Integer, Text, String, BigInteger, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# --------------------------------- #
# ~ ~ ~ ~ ~ ~ B O O K S ~ ~ ~ ~ ~ ~ #
# --------------------------------- #

# ~ ~ ~ ~ B O O K S ~ ~ ~ ~

# Association tables
works_authors = db.Table(
    'works_authors',
    Column('works_id', Integer, ForeignKey('works.id'), primary_key=True),
    Column('authors_id', Integer, ForeignKey('authors.id'), primary_key=True)
)


works_tags = db.Table(
    'works_tags',
    Column('works_id', Integer, ForeignKey('works.id'), primary_key=True),
    Column('tags_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

# Models
class Work(db.Model):
    __tablename__ = 'works'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    publisher = Column(Text)
    isbn = Column(BigInteger, unique=True)
    description = Column(Text)
    cover_url = Column(Text)
    
    # Relationships
    authors = relationship("Author", secondary=works_authors, back_populates="works")
    tags = relationship("Tag", secondary=works_tags, back_populates="works")
    copies = relationship("Copy", back_populates="work")


class Copy(db.Model):
    __tablename__ = 'copies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    work_id = Column(Integer, ForeignKey('works.id'), nullable=False)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'))
    condition = Column(String(50))
    acquired = Column(DateTime(timezone=True), default=func.now())
    lended_to = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    work = relationship("Work", back_populates="copies")
    location = relationship("Location", back_populates="copies")
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_copies")
    borrower = relationship("User", foreign_keys=[lended_to], back_populates="borrowed_copies")




# ~ ~ ~ A U T H O R S ~ ~ ~ ~
class Author(db.Model):
    __tablename__ = 'authors'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    primary_name = Column(Text, nullable=False)
    bio = Column(Text)
    
    # Relationships
    alt_names = relationship("AuthorName", back_populates="author")
    works = relationship("Work", secondary=works_authors, back_populates="authors")

    def __repr__(self):
        return 'Author object: "' + self.primary_name + '"'

class AuthorName(db.Model):
    __tablename__ = 'author_names'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(Integer, ForeignKey('authors.id'), nullable=False)
    alt_name = Column(Text)
    
    # Relationships
    author = relationship("Author", back_populates="alt_names")


# --------------------------------- #
# ~ ~ ~ ~ ~ D E T A I L S ~ ~ ~ ~ ~ #
# --------------------------------- #

class Tag(db.Model):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(Integer, ForeignKey('tags.id'))
    type = Column(String(50), nullable=False)
    label = Column(Text, nullable=False)
    description = Column(Text)
    
    # Relationships
    parent = relationship("Tag", remote_side=[id], back_populates="children")
    children = relationship("Tag", back_populates="parent")
    works = relationship("Work", secondary=works_tags, back_populates="tags")


class Location(db.Model):
    __tablename__ = 'locations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(Integer, ForeignKey('locations.id'))
    name = Column(Text, nullable=False)
    description = Column(Text)
    type = Column(String(50), nullable=False)
    
    # Relationships
    parent = relationship("Location", remote_side=[id], back_populates="children")
    children = relationship("Location", back_populates="parent")
    copies = relationship("Copy", back_populates="location")


# --------------------------------- #
# ~ ~ ~ ~ ~ ~ U S E R S ~ ~ ~ ~ ~ ~ #
# --------------------------------- #

class UserRole(Enum):
    VIEWER = 1
    EDITOR = 4
    ADMIN = 7

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, unique=True, nullable=False)
    email = Column(Text)
    password_hash = Column(Text)
    info = Column(Text)
    join_date = Column(DateTime, nullable=False)
    permissions = Column(Integer, nullable=False)

    # Relationships
    owned_copies = relationship("Copy", foreign_keys="Copy.owner_id", back_populates="owner")
    borrowed_copies = relationship("Copy", foreign_keys="Copy.lended_to", back_populates="borrower")

    # Properties
    @property
    def is_viewer(self):
        return self.permissions >= UserRole.VIEWER.value
    
    @property
    def is_contributor(self):
        return self.permissions >= UserRole.CONTRIBUTOR.value
    
    @property
    def is_editor(self):
        return self.permissions >= UserRole.EDITOR.value
    
    @property
    def is_admin(self):
        return self.permissions == UserRole.ADMIN.value

    @property
    def username(self):
        return self.name

    # Functions
    def can_edit_book(self, book):
        if self.is_admin or self.is_editor:
            return True
        if self.is_contributor and book.added_by_id == self.id:
            return True
        return False
    
    def can_manage_users(self):
        return self.is_admin

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



# --------------------------------- #
# ~ ~ ~ ~ F U N C T I O N S ~ ~ ~ ~ #
# --------------------------------- #

def create_tables(engine):
    db.create_all()


def get_works_by_author(session, author_name):
    return db.session.query(Work).join(works_authors).join(Author).outerjoin(AuthorName).filter(
        (Author.primary_name.ilike(f'%{author_name}%')) | 
        (AuthorName.alt_name.ilike(f'%{author_name}%'))
    ).all()