from flask import Flask, jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from Models import *
from flask_cors import CORS
from sqlalchemy.orm.exc import NoResultFound
from flask_migrate import Migrate

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"], methods=['GET', 'POST', 'PATCH', 'DELETE','PUT'], allow_headers=['Authorization', 'Content-Type', 'x-access-token'])
app.config['SECRET_KEY'] = 'c9cb13901b374ed2b4d9735e0e0a5fde'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zite.db'
migrate = Migrate(app, db)
db.init_app(app)

# Your models from the previous answer...

# User Authentication and Profile Management
@app.route('/register', methods=['POST'])
def register():
    # User registration route
    data = request.get_json()
    new_user = User(Username=data['username'], Password=data['password'], Email=data['email'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Registration Successful!'}), 201

@app.route('/login', methods=['POST'])
def login():
    # User login route
    data = request.get_json()
    user = User.query.filter_by(Username=data['username']).first()
    
    if user:
        if user.Password == data['password']:
            session['username'] = user.Username
            return jsonify({'message': 'Login Successful!'}), 200
    
    return jsonify({'message': 'Invalid Credentials!'}), 401


@app.route('/profile/<int:user_id>', methods=['GET'])
def profile(user_id):
    # View user profile route
    user = User.query.get(user_id)
    if user:
        return jsonify({
            'UserID': user.UserID,
            'Username': user.Username,
            'Email': user.Email,
            'ProfilePicture': user.ProfilePicture,
            'Bio': user.Bio,
            'ContactDetails': user.ContactDetails
            # Add other user attributes as needed
        }), 200
    return jsonify({'message': 'User not found!'}), 404

@app.route('/profile/<string:username>', methods=['GET'])
def profile_by_username(username):
    # View user profile by username route
    user = User.query.filter_by(Username=username).first()
    if user:
        return jsonify({
            'UserID': user.UserID,
            'Username': user.Username,
            'Email': user.Email,
            'ProfilePicture': user.ProfilePicture,
            'Bio': user.Bio,
            'ContactDetails': user.ContactDetails
            # Add other user attributes as needed
        }), 200
    return jsonify({'message': 'User not found!'}), 404


@app.route('/update_profile/<int:user_id>', methods=['PUT'])
def update_profile(user_id):
    # Update user profile route
    user = User.query.get(user_id)
    if user:
        data = request.get_json()
        # Update user attributes as needed...
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully!'}), 200
    return jsonify({'message': 'User not found!'}), 404

# Movies and Posts
@app.route('/post_movie', methods=['POST'])
def post_movie():
    # Post a watched movie route
    user = User.query.filter_by(Username=session['username']).first()
    if user:
        data = request.get_json()
        movie = Movie(Title=data['movie_title'])  # Add other attributes...
        db.session.add(movie)
        post = Post(author=user, movie=movie)  # Add other post attributes...
        db.session.add(post)
        db.session.commit()
        return jsonify({'message': 'Movie posted successfully!'}), 201

@app.route('/get_movies', methods=['GET'])
def get_movies():
    # Get all movies route
    movies = Movie.query.all()
    movie_list = []

    for movie in movies:
        movie_data = {
            'MovieID': movie.MovieID,
            'Title': movie.Title,
            'Genre': movie.Genre,
            'Director': movie.Director,
            'ReleaseYear': movie.ReleaseYear,
            'Synopsis': movie.Synopsis,
            'ImagePath': movie.ImagePath
        }
        movie_list.append(movie_data)

    return jsonify({'movies': movie_list}), 200

@app.route('/get_user_movies/<int:user_id>', methods=['GET'])
def get_user_movies(user_id):
    # Get watched movies of a specific user route
    user = User.query.get(user_id)
    if user:
        watched_movies = WatchedMovie.query.filter_by(UserID=user.UserID).all()
        movie_list = []
        for watched_movie in watched_movies:
            movie = Movie.query.get(watched_movie.MovieID)
            if movie:
                movie_data = {
                    'MovieID': movie.MovieID,
                    'Title': movie.Title,
                    'ImagePath': movie.ImagePath
                }
                movie_list.append(movie_data)
        return jsonify({'movies': movie_list}), 200
    return jsonify({'message': 'User not found!'}), 404

@app.route('/add_watched_movie', methods=['POST'])
def add_watched_movie():
    # Add a watched movie as a post route
    if 'username' not in session:
        return jsonify({'message': 'You must be logged in to add watched movies as posts!'}), 401

    user = User.query.filter_by(Username=session['username']).first()
    if not user:
        return jsonify({'message': 'User not found!'}), 404

    # Ask for user input for movie_id and user_id
    movie_id = input('Enter Movie ID: ')
    user_id = input('Enter User ID: ')

    # Check if the movie and user exist
    movie = Movie.query.get(movie_id)
    user = User.query.get(user_id)

    if not movie:
        return jsonify({'message': 'Movie not found!'}), 404

    if not user:
        return jsonify({'message': 'User not found!'}), 404
     
    # Create a new PrivatePost entry with the movie details
    post = PrivatePost(
        UserID=user.UserID,
        MovieID=movie.MovieID,
        Title=movie.Title,
        Genre=movie.Genre,
        Director=movie.Director,
        ReleaseYear=movie.ReleaseYear,
        Synopsis=movie.Synopsis,
        ImagePath=movie.ImagePath
    )

    # Commit the new post to the database
    db.session.add(post)
    db.session.commit()

    return "Post added successfully", 200


# Track a Watched Movie
@app.route('/track_movie', methods=['POST'])
def track_movie():
    # Track a watched movie route
    user = User.query.filter_by(Username=session['username']).first()
    if user:
        data = request.get_json()
        watched_movie = WatchedMovie(UserID=user.UserID, MovieID=data['movie_id'])
        db.session.add(watched_movie)
        db.session.commit()
        return jsonify({'message': 'Movie tracked successfully!'}), 200

@app.route('/watched_movies/<int:user_id>', methods=['GET'])
def get_watched_movies(user_id):
    # Check if the user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found!'}), 404

    # Retrieve all watched movies for the user
    watched_movies = WatchedMovie.query.filter_by(UserID=user_id).all()

    # Serialize the watched movies to JSON
    watched_movies_data = []
    for watched_movie in watched_movies:
        movie_data = {
            'MovieID': watched_movie.MovieID,
            'Title': watched_movie.movie.Title,
            'Genre': watched_movie.movie.Genre,
            'Director': watched_movie.movie.Director,
            'ReleaseYear': watched_movie.movie.ReleaseYear,
            'Synopsis': watched_movie.movie.Synopsis,
            'ImagePath': watched_movie.ImagePath
        }
        watched_movies_data.append(movie_data)

    return jsonify({'watched_movies': watched_movies_data}), 200

# Movie Clubs

@app.route('/clubs', methods=['GET'])
def get_all_clubs():
    # Get all movie clubs route
    clubs = Club.query.all()
    club_list = []

    for club in clubs:
        club_data = {
            'ClubID': club.ClubID,
            'Name': club.Name,
            'Genre': club.Genre,
            'OwnerID': club.OwnerID,
            # Add other club attributes as needed
        }
        club_list.append(club_data)

    return jsonify({'clubs': club_list}), 200

@app.route('/create_club', methods=['POST'])
def create_club():
    # Create a movie club route
    user = User.query.filter_by(Username=session['username']).first()
    if user:
        data_list = request.get_json()
        response_data = []
        
        for data in data_list:
            club = Club(Name=data['club_name'], Genre=data['genre'], OwnerID=data['owner_id'])
            db.session.add(club)
            response_data.append({'message': f'Club "{data["club_name"]}" created successfully!'})
        
        db.session.commit()
        return jsonify(response_data), 201
    else:
        return jsonify({'message': 'User not found!'}), 404

@app.route('/join_clubs_by_genre/<string:genre>', methods=['POST'])
def join_clubs_by_genre(genre):
    # Join movie clubs by genre route
    user = User.query.filter_by(Username=session['username']).first()
    if user:
        clubs = Club.query.filter_by(Genre=genre).all()
        if clubs:
            for club in clubs:
                existing_membership = Membership.query.filter_by(UserID=user.UserID, ClubID=club.ClubID).first()
                if existing_membership:
                    # Membership already exists for this user and club, skip it
                    continue
                
                membership = Membership(UserID=user.UserID, ClubID=club.ClubID)
                db.session.add(membership)
            
            db.session.commit()
            return jsonify({'message': f'Joined {len(clubs)} clubs in the {genre} genre successfully!'}), 200
        else:
            return jsonify({'message': f'No clubs found in the {genre} genre.'}), 404
    else:
        return jsonify({'message': 'User not found!'}), 404

@app.route('/join_club/<int:club_id>', methods=['POST'])
def join_club(club_id):
    # Join a movie club route
    user = User.query.filter_by(Username=session['username']).first()
    if user:
        membership = Membership(UserID=user.UserID, ClubID=club_id)
        db.session.add(membership)
        db.session.commit()
        return jsonify({'message': 'Joined club successfully!'}), 200


# Posts and Interactions

@app.route('/get_posts', methods=['GET'])
def get_posts():
    # Get all posts route
    posts = Post.query.all()
    post_list = [{'PostID': post.PostID, 'UserID': post.UserID, 'MovieID': post.MovieID} for post in posts]
    return jsonify({'posts': post_list}), 200

@app.route('/get_user_posts/<int:user_id>', methods=['GET'])
def get_user_posts(user_id):
    # Get posts from a specific user route
    user = User.query.get(user_id)
    if user:
        posts = Post.query.filter_by(UserID=user.UserID).all()
        post_list = []
        for post in posts:
            movie = Movie.query.get(post.MovieID)
            if movie:
                post_data = {
                    'PostID': post.PostID,
                    'UserID': post.UserID,
                    'MovieID': post.MovieID,
                    'Title': movie.Title,
                    'ImagePath': movie.ImagePath
                }
                post_list.append(post_data)
        return jsonify({'posts': post_list}), 200
    return jsonify({'message': 'User not found!'}), 404

@app.route('/view_post/<int:post_id>', methods=['GET'])
def view_post(post_id):
    # View a post route
    if 'username' in session:
        user = User.query.filter_by(Username=session['username']).first()
        if user:
            post = Post.query.get(post_id)
            
            if post:
                post_info = {
                    'PostID': post.PostID,
                    'Review': post.Review,
                    'Rating': post.Rating,
                    'ImagePath': post.ImagePath,
                    'Author': {
                        'UserID': post.author.UserID,
                        'Username': post.author.Username,
                        'ProfilePicture': post.author.ProfilePicture
                    },
                    'Movie': None,
                    'Comments': [],
                    'Likes': []
                }
                
                if post.movie:
                    post_info['Movie'] = {
                        'MovieID': post.movie.MovieID,
                        'Title': post.movie.Title,
                        'Genre': post.movie.Genre,
                        'Director': post.movie.Director,
                        'ReleaseYear': post.movie.ReleaseYear,
                        'Synopsis': post.movie.Synopsis,
                        'ImagePath': post.movie.ImagePath
                    }
                
                comments = Comment.query.filter_by(PostID=post.PostID).all()
                likes = Like.query.filter_by(PostID=post.PostID).all()
                
                for comment in comments:
                    post_info['Comments'].append({
                        'CommentID': comment.CommentID,
                        'CommentText': comment.CommentText,
                        'Commenter': {
                            'UserID': comment.commenter.UserID,
                            'Username': comment.commenter.Username
                        }
                    })
                
                for like in likes:
                    post_info['Likes'].append({
                        'LikeID': like.LikeID,
                        'Liker': {
                            'UserID': like.liker.UserID,
                            'Username': like.liker.Username
                        }
                    })
                
                return jsonify(post_info), 200
            
    return jsonify({'message': 'Unauthorized or post not found!'}), 401

@app.route('/share_post/<int:post_id>', methods=['GET', 'POST'])
def share_post(post_id):
    # Share a post route
    if request.method == 'GET':
        # Fetch the post by its ID
        post = Post.query.get(post_id)

        if post:
            # Prepare the detailed post information
            post_info = {
                'PostID': post.PostID,
                'Review': post.Review,
                'Rating': post.Rating,
                'ImagePath': post.ImagePath,
                'Author': {
                    'UserID': post.author.UserID,
                    'Username': post.author.Username,
                    'ProfilePicture': post.author.ProfilePicture
                },
                'Movie': None,
                'Comments': [],
                'Likes': []
            }

            # If the post is related to a movie, include movie information
            if post.movie:
                post_info['Movie'] = {
                    'MovieID': post.movie.MovieID,
                    'Title': post.movie.Title,
                    'Genre': post.movie.Genre,
                    'Director': post.movie.Director,
                    'ReleaseYear': post.movie.ReleaseYear,
                    'Synopsis': post.movie.Synopsis,
                    'ImagePath': post.movie.ImagePath
                }

            # Fetch and include comments and likes associated with the post
            comments = Comment.query.filter_by(PostID=post.PostID).all()
            likes = Like.query.filter_by(PostID=post.PostID).all()

            for comment in comments:
                post_info['Comments'].append({
                    'CommentID': comment.CommentID,
                    'CommentText': comment.CommentText,
                    'Commenter': {
                        'UserID': comment.commenter.UserID,
                        'Username': comment.commenter.Username
                    }
                })

            for like in likes:
                post_info['Likes'].append({
                    'LikeID': like.LikeID,
                    'Liker': {
                        'UserID': like.liker.UserID,
                        'Username': like.liker.Username
                    }
                })

            return jsonify(post_info), 200

        return jsonify({'message': 'Post not found!'}), 404

    elif request.method == 'POST':
        # Check if the user is authenticated
        if 'username' not in session:
            return jsonify({'message': 'You must be logged in to share posts!'}), 401

    user = User.query.filter_by(Username=session['username']).first()
    if not user:
        return jsonify({'message': 'User not found!'}), 404

    # Check if the post with the specified post_id exists
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'message': 'Post not found!'}), 404

    # Create a new shared post for the user with all columns of the original post
    shared_post = SharedPost(
        UserID=user.UserID,
        OriginalPostID=post.PostID  # Link the shared post to the original post
    )
    db.session.add(shared_post)
    db.session.commit()

    # Include all columns from the original post in the response
    shared_post_info = {
        'SharedPostID': shared_post.SharedPostID,
        'UserID': shared_post.UserID,
        'OriginalPostID': shared_post.OriginalPostID,
        # Include other columns from the original post here
        'Review': post.Review,
        'Rating': post.Rating,
        'ImagePath': post.ImagePath,
        'Author': {
            'UserID': post.author.UserID,
            'Username': post.author.Username,
            'ProfilePicture': post.author.ProfilePicture
        },
        'Movie': None,
        'Comments': [],
        'Likes': []
    }

    # If the post is related to a movie, include movie information
    if post.movie:
        shared_post_info['Movie'] = {
            'MovieID': post.movie.MovieID,
            'Title': post.movie.Title,
            'Genre': post.movie.Genre,
            'Director': post.movie.Director,
            'ReleaseYear': post.movie.ReleaseYear,
            'Synopsis': post.movie.Synopsis,
            'ImagePath': post.movie.ImagePath
        }

    # Fetch and include comments and likes associated with the original post
    comments = Comment.query.filter_by(PostID=post.PostID).all()
    likes = Like.query.filter_by(PostID=post.PostID).all()

    for comment in comments:
        shared_post_info['Comments'].append({
            'CommentID': comment.CommentID,
            'CommentText': comment.CommentText,
            'Commenter': {
                'UserID': comment.commenter.UserID,
                'Username': comment.commenter.Username
            }
        })

    for like in likes:
        shared_post_info['Likes'].append({
            'LikeID': like.LikeID,
            'Liker': {
                'UserID': like.liker.UserID,
                'Username': like.liker.Username
            }
        })

    return jsonify(shared_post_info), 201

# Like a Post
@app.route('/like_post/<int:post_id>', methods=['POST'])
def like_post(post_id):
    # Like a post route
    if 'username' in session:
        user = User.query.filter_by(Username=session['username']).first()
        if user:
            post = Post.query.get(post_id)
            if post:
                like = Like(PostID=post.PostID, UserID=user.UserID)
                db.session.add(like)
                db.session.commit()
                return jsonify({'message': 'Liked post successfully!'}), 200
            return jsonify({'message': 'Post not found!'}), 404
        return jsonify({'message': 'User not found!'}), 404
    else:
        return jsonify({'message': 'You must be logged in to like a post!'}), 401

# Comment on a Post
@app.route('/comment_on_post/<int:post_id>', methods=['POST'])
def comment_on_post(post_id):
    # Comment on a post route
    if 'username' in session:
        user = User.query.filter_by(Username=session['username']).first()
        if user:
            data = request.get_json()
            comment = Comment(PostID=post_id, UserID=user.UserID, CommentText=data['comment_text'])
            db.session.add(comment)
            db.session.commit()
            return jsonify({'message': 'Commented successfully!'}), 200
        return jsonify({'message': 'User not found!'}), 404
    else:
        return jsonify({'message': 'You must be logged in to comment!'}), 401

# Follow a User
@app.route('/follow_user/<int:followee_id>', methods=['POST'])
def follow_user(followee_id):
    # Follow a user route
    user = User.query.filter_by(Username=session['username']).first()
    if user:
        follow = Follow(FollowerID=user.UserID, FolloweeID=followee_id)
        db.session.add(follow)
        db.session.commit()
        return jsonify({'message': 'Followed user successfully!'}), 200

# Unfollow a User
@app.route('/unfollow_user/<int:followee_id>', methods=['DELETE'])
def unfollow_user(followee_id):
    # Unfollow a user route
    user = User.query.filter_by(Username=session['username']).first()
    if user:
        follow = Follow.query.filter_by(FollowerID=user.UserID, FolloweeID=followee_id).first()
        if follow:
            db.session.delete(follow)
            db.session.commit()
            return jsonify({'message': 'Unfollowed user successfully!'}), 200




if __name__ == '__main__':
    app.run(debug=True)
