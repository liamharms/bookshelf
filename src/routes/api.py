from flask import Blueprint, request, jsonify
from models import db
from models.models import Work, Copy, Author, Tag, Location
from sqlalchemy import or_, cast, String
from fuzzywuzzy import fuzz
import requests

api_bp = Blueprint('api', __name__)

@api_bp.route('/search')
def api_search():
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'books': []})
    
    try:
        print(f"Search query: '{query}'")
        
        search_conditions = []
        
        # Direct field searches with proper casting
        search_conditions.extend([
            Book.title.ilike(f'%{query}%'),
            cast(Book.isbn, String).ilike(f'%{query}%'),
            Book.description.ilike(f'%{query}%')
        ])
        
        # Relationship searches
        search_conditions.extend([
            Book.authors.any(Author.name.ilike(f'%{query}%')),
            Book.tags.any(Tag.label.ilike(f'%{query}%')),
            Book.location.has(Location.name.ilike(f'%{query}%'))
        ])
        
        # Combine with OR
        search_filter = or_(*search_conditions)
        
        books = Book.query.filter(search_filter).all()
        print(f"Found {len(books)} books")
        
        book_list = []
        for book in books:
            try:
                book_data = {
                    'id': book.id,
                    'title': book.title or '',
                    'isbn': book.isbn or '',
                    'description': book.description or '',
                    'cover_url': book.cover_url or '',
                    'authors': [{'id': a.id, 'name': a.name} for a in (book.authors or [])],
                    'tags': [{'id': t.id, 'label': t.label} for t in (book.tags or [])],
                    'location': {'id': book.location.id, 'name': book.location.name} if book.location else None
                }
                book_list.append(book_data)
            except Exception as e:
                print(f"Error processing book {book.id}: {e}")
                continue
        
        print(f"Returning {len(book_list)} processed books")
        return jsonify({'books': book_list})
        
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({'error': str(e), 'books': []}), 500


@api_bp.route('/isbn-lookup/<isbn>')
def isbn_lookup(isbn):
    """Look up book information by ISBN"""
    try:
        # Try Google Books API first
        google_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        response = requests.get(google_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                book = data['items'][0]['volumeInfo']
                return jsonify({
                    'success': True,
                    'title': book.get('title', ''),
                    'authors': book.get('authors', []),
                    'description': book.get('description', ''),
                    'cover_url': book.get('imageLinks', {}).get('thumbnail', '').replace('http:', 'https:'),
                    'categories': book.get('categories', [])
                })
        
        # Fallback to Open Library
        openlibrary_url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
        response = requests.get(openlibrary_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            book_key = f"ISBN:{isbn}"
            if data.get(book_key):
                book = data[book_key]
                return jsonify({
                    'success': True,
                    'title': book.get('title', ''),
                    'authors': [a['name'] for a in book.get('authors', [])],
                    'description': book.get('notes', '') or book.get('subtitle', ''),
                    'cover_url': book.get('cover', {}).get('medium', ''),
                    'categories': [s['name'] for s in book.get('subjects', [])]
                })
        
        return jsonify({'success': False, 'error': 'Book not found'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
@api_bp.route('/authors/search', methods=['POST'])
def search_authors():
    """Find similar authors using fuzzy matching"""
    try:
        data = request.get_json()
        search_name = data.get('name', '').strip()
        
        if not search_name:
            return jsonify({'success': False, 'error': 'Name is required'})
        
        # Get all authors with their alternate names
        authors = db.session.query(Author).all()
        matches = []
        print(authors)
        for author in authors:
            print(author)
            # Check primary name with multiple methods
            primary_ratio = fuzz.ratio(search_name.lower(), author.primary_name.lower())
            primary_partial = fuzz.partial_ratio(search_name.lower(), author.primary_name.lower())
            primary_token_sort = fuzz.token_sort_ratio(search_name.lower(), author.primary_name.lower())
            
            # Use the best score from all methods
            primary_score = max(primary_ratio, primary_partial, primary_token_sort)
            
            # Check alternate names
            alt_scores = []
            for alt_name in author.alt_names:
                alt_ratio = fuzz.ratio(search_name.lower(), alt_name.alt_name.lower())
                alt_partial = fuzz.partial_ratio(search_name.lower(), alt_name.alt_name.lower())
                alt_token_sort = fuzz.token_sort_ratio(search_name.lower(), alt_name.alt_name.lower())
                alt_scores.append(max(alt_ratio, alt_partial, alt_token_sort))
            
            # Use the best score across all names
            best_score = max([primary_score] + alt_scores) if alt_scores else primary_score

            if best_score >= 70:  # Threshold for similarity
                matches.append({
                    'id': author.id,
                    'name': author.primary_name,
                    'score': best_score
                })
        
        # Sort by score and return top 2
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return jsonify({
            'success': True,
            'matches': matches[:2]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@api_bp.route('/authors/create', methods=['POST'])
def create_author():
    """Create a new author"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'success': False, 'error': 'Name is required'})
        
        # Check if author already exists
        existing = db.session.query(Author).filter(
            Author.primary_name.ilike(name)
        ).first()
        
        if existing:
            return jsonify({'success': False, 'error': 'Author already exists'})
        
        author = Author(primary_name=name)
        db.session.add(author)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'author': {
                'id': author.id,
                'name': author.primary_name
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})


@api_bp.route('/tags/search', methods=['POST'])
def search_tags():
    """Find similar tags using fuzzy matching"""
    try:
        data = request.get_json()
        search_label = data.get('label', '').strip()
        
        if not search_label:
            return jsonify({'success': False, 'error': 'Label is required'})
        
        # Get all tags
        tags = db.session.query(Tag).all()
        matches = []
        
        for tag in tags:
            # Use multiple fuzzy matching methods
            ratio_score = fuzz.ratio(search_label.lower(), tag.label.lower())
            partial_score = fuzz.partial_ratio(search_label.lower(), tag.label.lower())
            token_sort_score = fuzz.token_sort_ratio(search_label.lower(), tag.label.lower())
            
            # Use the best score from all methods
            best_score = max(ratio_score, partial_score, token_sort_score)
            
            if best_score >= 70:  # Threshold for similarity
                matches.append({
                    'id': tag.id,
                    'label': tag.label,
                    'type': tag.type,
                    'score': best_score
                })
        
        # Sort by score and return top 2
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return jsonify({
            'success': True,
            'matches': matches[:2]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@api_bp.route('/tags/create', methods=['POST'])
def create_tag():
    """Create a new tag"""
    try:
        data = request.get_json()
        label = data.get('label', '').strip()
        tag_type = data.get('type', 'genre').strip()  # Default to 'genre'
        
        if not label:
            return jsonify({'success': False, 'error': 'Label is required'})
        
        # Check if tag already exists
        existing = db.session.query(Tag).filter(
            Tag.label.ilike(label)
        ).first()
        
        if existing:
            return jsonify({'success': False, 'error': 'Tag already exists'})
        
        tag = Tag(label=label, type=tag_type)
        db.session.add(tag)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'tag': {
                'id': tag.id,
                'label': tag.label,
                'type': tag.type
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})