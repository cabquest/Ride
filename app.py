from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_cors import CORS
from models import db, Ride, Driver, User, Liveloc
import requests
from datetime import datetime
import math, os, random
from dotenv import load_dotenv
from flask_mail import Mail, Message


load_dotenv()

def create_app():

    app = Flask(__name__)


    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://ride:ride@localhost:33068/ride'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = 'cabquest.buisness@gmail.com'
    app.config['MAIL_PASSWORD'] = os.environ["GOOGLE_APP_PASSWORD"]
        
    migrate = Migrate(app, db)
    db.init_app(app)
    mail = Mail(app)
    CORS(app, supports_credentials=True)

    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

    def generate_otp():
        otp = random.randint(11111,99999)
        print(otp)
        return otp
    
    def send_mail(email,fullname,otp):
        msg = Message('Your OTP Code', sender='cabquest.buisness@gmail.com', recipients=[email])
        msg.body = f"""
            Thank you for choosing our taxi service!

            Your confirmation code is :

            {otp}

            Thank you,
            cabQuest Team
            """
        try:
            mail.send(msg)
            return 'Email sent successfully!'
        except Exception as e:
            return str(e)

    def get_location_name(lat, lon, api_key):
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                return data['results'][0]['formatted_address']
            else:
                return None
        else:
            return None

    def get_coordinates(place_name, api_key):
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={place_name}&key={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(data)
            if data['results']:
                location = data['results'][0]['geometry']['location']
                return location['lat'], location['lng']
            else:
                return None, None
        else:
            return None, None
        
    def haversine(coord1, coord2):

        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        dlat = lat2 - lat1 
        dlon = lon2 - lon1 
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a)) 
        r = 6371 
        distance_km = c * r
        
        return round(distance_km, 2)

    @app.route('/')
    def home():
        return jsonify({'message':'okkk'})

    @app.route('/createride',methods = ['POST'])
    def driveaccept():
        data = request.get_json()
        print(data)
        lat,log = get_coordinates(data['pick_up_location'],GOOGLE_MAPS_API_KEY)
        print(lat,log)
        currentlocation = get_location_name(data['current_location']['lat'],data['current_location']['lon'],GOOGLE_MAPS_API_KEY )
        pickup_km = haversine((data['current_location']['lat'],data['current_location']['lon']),(lat,log))
        print(currentlocation, pickup_km)
        ride = Ride(
            user_id = data['user_id'],
            driver_id = data['driver_id'],
            vehicle_type = data['vehicle_type'],
            current_location = currentlocation,
            pick_up_location = data['pick_up_location'],
            drop_location = data['drop_location'],
            pickup_km = pickup_km,
            total_km =  float(data['total_km'].replace(' km', '')),
            status = 'ride started',
            fare = float(data['fare']),
            created_at = datetime.now()
        )
        db.session.add(ride)
        db.session.commit()

        return jsonify({'message':'okkk'})

    @app.route('/checkride',methods = ["POST"])
    def checkride():
        data = request.get_json()
        print(data)
        ride = Ride.query.filter(
            Ride.user_id == data['userid'],
            Ride.status.in_(['ride started', 'driver arrived'])
        ).first()
        print(ride)
        if ride:
            return jsonify({'message':'ridestarted'})
        return jsonify({'message':'okkk'})  

    @app.route('/getride', methods = ['POST'])
    def getride():
        data = request.get_json()
        driver = Driver.query.filter_by( email = data['email']).first()
        ride = Ride.query.filter(
            Ride.driver_id == driver.id,
            Ride.status.in_(['ride started', 'driver arrived', 'trip started'])
        ).first()
        rides = {
            'id':ride.id,
            'vehicle_type':ride.vehicle_type,
            'current_location':ride.current_location,
            'pick_up_location':ride.pick_up_location,
            'drop_location':ride.drop_location,
            'pickupkm':ride.pickup_km,
            'total_km':ride.total_km,
            'fare':ride.fare
        }
        return jsonify({'message':'okkk','ride':rides})
    
    @app.route('/getride2', methods = ['POST'])
    def getride2():
        data = request.get_json()
        driver = User.query.filter_by( email = data['email']).first()
        ride = Ride.query.filter(
            Ride.user_id == driver.id,
            Ride.status.in_(['ride started', 'driver arrived', 'trip started'])
        ).first()
        rides = {
            'id':ride.id,
            'vehicle_type':ride.vehicle_type,
            'current_location':ride.current_location,
            'pick_up_location':ride.pick_up_location,
            'drop_location':ride.drop_location,
            'pickupkm':ride.pickup_km,
            'total_km':ride.total_km,
            'fare':ride.fare
        }
        return jsonify({'message':'okkk','ride':rides})

    @app.route('/getrideuser', methods = ['POST'])
    def getrideuser():
        data = request.get_json()
        user = User.query.filter_by( email = data['email']).first()
        ride = Ride.query.filter(
            Ride.user_id == user.user_id,
            Ride.status.in_(['ride started', 'driver arrived', 'trip started'])
        ).first()
        driver = Driver.query.filter_by(driver_id = ride.driver_id).first()
        mode = 'driving'
        url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={ride.current_location}&destinations={ride.pick_up_location}&mode={mode}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()

        if data['status'] != 'OK':
            return jsonify({"error": "Error fetching data from Google Maps API", "details": data}), 500

        elements = data['rows'][0]['elements'][0]

        if elements['status'] != 'OK':
            return jsonify({"error": "Error fetching travel time from Google Maps API", "details": elements}), 500

        travel_time = elements['duration']['text']
        travel_distance = elements['distance']['text']
       
        live = Liveloc.query.filter_by(driver_id = ride.driver_id).first()

        rides = {
            'driver_name':driver.fullname,
            'travel_time':travel_time,
            'vehicle_type':ride.vehicle_type,
            'current_location':ride.current_location,
            'pick_up_location':ride.pick_up_location,
            'pickupkm':ride.pickup_km,
            'total_km':ride.total_km,
            'fare':ride.fare,
            'live':{'lat':live.latitude,'lng':live.longitude}
        }
        return jsonify({'message':'okkk','ride':rides})

    @app.route('/liveloc',methods = ['POST'])
    def liveloc():
        data = request.get_json()
        driver = Driver.query.filter_by( email = data['email']).first()
        ride = Liveloc.query.filter_by( driver_id = driver.driver_id).first()
        if ride:
            ride.latitude = data['coords']['lat']
            ride.longitude = data['coords']['lng']
            db.session.commit()
        else:
            liv = Liveloc(driver_id = driver.id, latitude = data['coords']['lat'], longitude = data['coords']['lng'])
            db.session.add(liv)
            db.session.commit()
        return jsonify({'message':'hello2'})

    @app.route('/driverarrived',methods = ["POST"])
    def driverarrived():
        data = request.get_json()
        driver = Driver.query.filter_by( email = data['email']).first()
        ride = Ride.query.filter(
            Ride.driver_id == driver.id,
            Ride.status.in_(['ride started', 'driver arrived'])
        ).first()
        user = User.query.filter_by(user_id = ride.user_id).first()
        ride.status = 'driver arrived'
        db.session.commit()
        otp = generate_otp()
        # send_mail(user.email,user.fullname,otp)
        return jsonify({'message':'ok','otp':otp})
    
    @app.route('/tripstarted',methods = ["POST"])
    def tripstarted():
        data = request.get_json()
        driver = Driver.query.filter_by(email = data['email']).first()
        ride = Ride.query.filter(
            Ride.driver_id == driver.id,
            Ride.status == 'driver arrived'
        ).first()
        ride.status = 'trip started'
        db.session.commit()
        return jsonify({'message':'ok'})
    
    @app.route('/istripstarted',methods = ['POST'])
    def istripstarted():
        data = request.get_json()
        user = User.query.filter_by(email = data['email']).first()
        ride = Ride.query.filter(
            Ride.user_id == user.id,
            Ride.status == 'trip started'
        ).first()     
        if ride:
            return jsonify({'message':'trip started'})
        return jsonify({'message':'ok'})

    @app.route('/getlive',methods = ["POST"])
    def getlive():
        try:
            data = request.get_json()
            user = User.query.filter_by(email = data['email']).first()
            ride = Ride.query.filter(Ride.user_id == user.id, Ride.status == 'trip started').first()
            live = Liveloc.query.filter_by(driver_id = ride.driver_id).first()
            return jsonify({'latitude':float(live.latitude),'longitude':float(live.longitude)})
        except:
            return jsonify({'message':'ok'})

    @app.route('/isridefinish', methods = ["POST"])
    def isridefinish():
        data = request.get_json()
        user = User.query.filter_by(email = data['email']).first()
        ride = Ride.query.filter(Ride.user_id == user.id, Ride.status == 'trip completed').first()
        if ride:
            return jsonify({'message':'trip completed'})
        return jsonify({'message':'ok'})
    
    @app.route('/ridefinish',methods = ['POST'])
    def ridefinish():
        data = request.get_json()
        driver = Driver.query.filter_by(email = data['email']).first()
        ride = Ride.query.filter_by(driver_id = driver.id).first()
        ride.status = 'trip completed'
        db.session.commit()
        return jsonify({'message':'ok'})

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=9640)