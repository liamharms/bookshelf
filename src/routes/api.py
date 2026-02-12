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
    search_type = request.args.get('type', 'all')
    date_range = request.args.get('date', '')
    
    if not query:
        return jsonify({'books': []})
    
    try:
        print(f"Search query: '{query}', type: '{search_type}', date_range: '{date_range}'")
        
        search_conditions = []
        
        # Apply filters based on search type
        if search_type == 'all' or search_type is None:
            # Direct field searches with proper casting
            search_conditions.extend([
                Work.title.ilike(f'%{query}%'),
                cast(Work.isbn, String).ilike(f'%{query}%'),
                Work.description.ilike(f'%{query}%')
            ])
        elif search_type == 'title':
            search_conditions.append(Work.title.ilike(f'%{query}%'))
        elif search_type == 'authors':
            search_conditions.append(Work.authors.any(Author.primary_name.ilike(f'%{query}%')))
        elif search_type == 'tags':
            search_conditions.append(Work.tags.any(Tag.label.ilike(f'%{query}%')))
        elif search_type == 'isbn':
            search_conditions.append(cast(Work.isbn, String).ilike(f'%{query}%'))
        elif search_type == 'location':
            search_conditions.append(Work.copies.any(Copy.location.has(Location.name.ilike(f'%{query}%'))))
        elif search_type == 'description':
            search_conditions.append(Work.description.ilike(f'%{query}%'))
        
        # Always include relationship searches for better results
        if search_type != 'authors':
            search_conditions.extend([
                Work.authors.any(Author.primary_name.ilike(f'%{query}%')),
                Work.tags.any(Tag.label.ilike(f'%{query}%')),
                Work.copies.any(Copy.location.has(Location.name.ilike(f'%{query}%')))
            ])
        
        # Apply date range filter
        if date_range:
            try:
                if date_range == 'recent':
                    # Last 30 days
                    from datetime import datetime, timedelta
                    start_date = datetime.now() - timedelta(days=30)
                    search_conditions.append(Work.copies.any(Copy.acquired >= start_date))
                elif date_range == 'this_month':
                    # This calendar month
                    from datetime import datetime
                    now = datetime.now()
                    if now.month == 1:
                        # Go to previous month
                        start_date = datetime(year=now.year-1, month=12, day=1)
                    else:
                        # Go to start of this month
                        start_date = datetime(year=now.year, month=now.month, day=1)
                elif date_range == 'last_month':
                    # Previous calendar month
                    from datetime import datetime
                    now = datetime.now()
                    if now.month == 1:
                        start_date = datetime(year=now.year-1, month=12, day=1)
                    else:
                        start_date = datetime(year=now.year, month=now.month-1, day=1)
                else:
                    # Default - no date filtering
                    pass
            except Exception as e:
                print(f"Error parsing date range '{date_range}': {e}")
        
        # Combine with OR
        search_filter = or_(*search_conditions)
        
        works = Work.query.filter(search_filter).all()
        print(f"Found {len(works)} works")
        
        work_list = []
        for work in works:
            try:
                work_data = {
                    'id': work.id,
                    'title': work.title or '',
                    'isbn': work.isbn or '',
                    'description': work.description or '',
                    'cover_url': work.cover_url or '',
                    'authors': [{'id': a.id, 'name': a.primary_name} for a in (work.authors or [])],
                    'tags': [{'id': t.id, 'label': t.label} for t in (work.tags or [])],
                    'location': {'id': work.location.id, 'name': work.location.name} if work.location else None,
                    'copies_count': len(work.copies or [])
                }
                work_list.append(work_data)
            except Exception as e:
                print(f"Error processing work {work.id}: {e}")
                continue
        
        print(f"Returning {len(work_list)} processed works")
        return jsonify({'books': work_list})
        
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({'error': str(e), 'books': []}), 500

@api_bp.route('/search/works')
def api_search_works():
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'works': []})
    
    try:
        search_conditions = [
            Work.title.ilike(f'%{query}%'),
            cast(Work.isbn, String).ilike(f'%{query}%'),
            Work.description.ilike(f'%{query}%'),
            Work.authors.any(Author.primary_name.ilike(f'%{query}%')),
            Work.tags.any(Tag.label.ilike(f'%{query}%'))
        ]
        
        search_filter = or_(*search_conditions)
        works = Work.query.filter(search_filter).limit(50).all()
        
        work_list = []
        for work in works:
            work_data = {
                'id': work.id,
                'title': work.title or '',
                'isbn': work.isbn or '',
                'authors': [a.primary_name for a in (work.authors or [])],
                'copies_count': len(work.copies or [])
            }
            work_list.append(work_data)
        
        return jsonify({'works': work_list})
        
    except Exception as e:
        print(f"Works search error: {e}")
        return jsonify({'error': str(e), 'works': []}), 500

@api_bp.route('/search/copies')
def api_search_copies():
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'copies': []})
    
    try:
        search_conditions = [
            Work.title.ilike(f'%{query}%'),
            Work.authors.any(Author.primary_name.ilike(f'%{query}%')),
            Location.name.ilike(f'%{query}%')
        ]
        
        search_filter = or_(*search_conditions)
        copies = Copy.query.join(Work).join(Location).filter(search_filter).limit(50).all()
        
        copy_list = []
        for copy in copies:
            copy_data = {
                'id': copy.id,
                'work_title': copy.work.title if copy.work else '',
                'work_id': copy.work.id if copy.work else None,
                'location': copy.location.name if copy.location else '',
                'location_id': copy.location.id if copy.location else None,
                'condition': copy.condition,
                'authors': [a.primary_name for a in (copy.work.authors if copy.work else [])]
            }
            copy_list.append(copy_data)
        
        return jsonify({'copies': copy_list})
        
    except Exception as e:
        print(f"Copies search error: {e}")
        return jsonify({'error': str(e), 'copies': []}), 500

@api_bp.route('/search/authors')
def api_search_authors():
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'authors': []})
    
    try:
        search_conditions = [
            Author.primary_name.ilike(f'%{query}%'),
            Author.bio.ilike(f'%{query}%')
        ]
        
        search_filter = or_(*search_conditions)
        authors = Author.query.filter(search_filter).limit(50).all()
        
        author_list = []
        for author in authors:
            work_count = len(author.works or [])
            author_data = {
                'id': author.id,
                'primary_name': author.primary_name or '',
                'bio': author.bio or '',
                'work_count': work_count
            }
            author_list.append(author_data)
        
        return jsonify({'authors': author_list})
        
    except Exception as e:
        print(f"Authors search error: {e}")
        return jsonify({'error': str(e), 'authors': []}), 500

@api_bp.route('/search/tags')
def api_search_tags():
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'tags': []})
    
    try:
        search_conditions = [
            Tag.label.ilike(f'%{query}%'),
            Tag.description.ilike(f'%{query}%')
        ]
        
        search_filter = or_(*search_conditions)
        tags = Tag.query.filter(search_filter).limit(50).all()
        
        tag_list = []
        for tag in tags:
            work_count = len(tag.works or [])
            tag_data = {
                'id': tag.id,
                'label': tag.label or '',
                'description': tag.description or '',
                'parent_id': tag.parent_id,
                'work_count': work_count
            }
            tag_list.append(tag_data)
        
        return jsonify({'tags': tag_list})
        
    except Exception as e:
        print(f"Tags search error: {e}")
        return jsonify({'error': str(e), 'tags': []}), 500

@api_bp.route('/search/locations')
def api_search_locations():
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'locations': []})
    
    try:
        search_conditions = [
            Location.name.ilike(f'%{query}%'),
            Location.description.ilike(f'%{query}%')
        ]
        
        search_filter = or_(*search_conditions)
        locations = Location.query.filter(search_filter).limit(50).all()
        
        location_list = []
        for location in locations:
            copy_count = len(location.copies or [])
            location_data = {
                'id': location.id,
                'name': location.name or '',
                'description': location.description or '',
                'parent_id': location.parent_id,
                'copy_count': copy_count
            }
            location_list.append(location_data)
        
        return jsonify({'locations': location_list})
        
    except Exception as e:
        print(f"Locations search error: {e}")
        return jsonify({'error': str(e), 'locations': []}), 500
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')
    date_range = request.args.get('date', '')
    
    if not query:
        return jsonify({'books': []})
    
    try:
        print(f"Search query: '{query}', type: '{search_type}', date_range: '{date_range}'")
        
        search_conditions = []
        
        # Apply filters based on search type
        if search_type == 'all' or search_type is None:
            # Direct field searches with proper casting
            search_conditions.extend([
                Work.title.ilike(f'%{query}%'),
                cast(Work.isbn, String).ilike(f'%{query}%'),
                Work.description.ilike(f'%{query}%')
            ])
        elif search_type == 'title':
            search_conditions.append(Work.title.ilike(f'%{query}%'))
        elif search_type == 'authors':
            search_conditions.append(Work.authors.any(Author.primary_name.ilike(f'%{query}%')))
        elif search_type == 'tags':
            search_conditions.append(Work.tags.any(Tag.label.ilike(f'%{query}%')))
        elif search_type == 'isbn':
            search_conditions.append(cast(Work.isbn, String).ilike(f'%{query}%'))
        elif search_type == 'location':
            search_conditions.append(Work.copies.any(Copy.location.has(Location.name.ilike(f'%{query}%'))))
        elif search_type == 'description':
            search_conditions.append(Work.description.ilike(f'%{query}%'))
        
        # Always include relationship searches for better results
        if search_type != 'authors':
            search_conditions.extend([
                Work.authors.any(Author.primary_name.ilike(f'%{query}%')),
                Work.tags.any(Tag.label.ilike(f'%{query}%')),
                Work.copies.any(Copy.location.has(Location.name.ilike(f'%{query}%')))
            ])
        
        # Apply date range filter
        if date_range:
            try:
                if date_range == 'recent':
                    # Last 30 days
                    from datetime import datetime, timedelta
                    start_date = datetime.now() - timedelta(days=30)
                    search_conditions.append(Work.copies.any(Copy.acquired >= start_date))
                elif date_range == 'this_month':
                    # This calendar month
                    from datetime import datetime
                    now = datetime.now()
                    if now.month == 1:
                        # Go to previous month
                        start_date = datetime(year=now.year-1, month=12, day=1)
                    else:
                        # Go to start of this month
                        start_date = datetime(year=now.year, month=now.month, day=1)
                elif date_range == 'last_month':
                    # Previous calendar month
                    from datetime import datetime
                    now = datetime.now()
                    if now.month == 1:
                        start_date = datetime(year=now.year-1, month=12, day=1)
                    else:
                        start_date = datetime(year=now.year, month=now.month-1, day=1)
                else:
                    # Default - no date filtering
                    pass
            except Exception as e:
                print(f"Error parsing date range '{date_range}': {e}")
        
        # Combine with OR
        search_filter = or_(*search_conditions)
        
        works = Work.query.filter(search_filter).all()
        print(f"Found {len(works)} works")
        
        work_list = []
        for work in works:
            try:
                work_data = {
                    'id': work.id,
                    'title': work.title or '',
                    'isbn': work.isbn or '',
                    'description': work.description or '',
                    'cover_url': work.cover_url or '',
                    'authors': [{'id': a.id, 'name': a.primary_name} for a in (work.authors or [])],
                    'tags': [{'id': t.id, 'label': t.label} for t in (work.tags or [])],
                    'location': {'id': work.location.id, 'name': work.location.name} if work.location else None,
                    'copies_count': len(work.copies or [])
                }
                work_list.append(work_data)
            except Exception as e:
                print(f"Error processing work {work.id}: {e}")
                continue
        
        print(f"Returning {len(work_list)} processed works")
        return jsonify({'books': work_list})
        
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({'error': str(e), 'books': []}), 500
