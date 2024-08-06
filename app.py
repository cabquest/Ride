from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_cors import CORS
from models import db, Ride, Driver, User, Liveloc, CancelReason, Wallet
import requests
from datetime import datetime
import math, os, random
from dotenv import load_dotenv
from flask_mail import Mail, Message
from rabbitmq_producer import publish_message
from sqlalchemy import func, extract, case, not_
from datetime import datetime, timedelta 
import calendar
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import cast, Date

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
        try:
            total_km = float(data['total_km'].replace(' km', ''))
        except:
            total_km = data['total_km']
        ride = Ride(
            user_id = data['user_id'],
            driver_id = data['driver_id'],
            vehicle_type = data['vehicle_type'],
            current_location = currentlocation,
            pick_up_location = data['pick_up_location'],
            drop_location = data['drop_location'],
            pickup_km = pickup_km,
            total_km =  total_km,
            status = 'ride started',
            fare = float(data['fare']),
            created_at = datetime.now()
        )
        db.session.add(ride)
        db.session.commit()
        data = {'user_id' : data['user_id'],
            "driver_id" : data['driver_id'],
            "vehicle_type" : data['vehicle_type'],
            "current_location" : currentlocation,
            "pick_up_location" : data['pick_up_location'],
            "drop_location" : data['drop_location'],
            "pickup_km" : pickup_km,
            "total_km" : total_km,
            "status" : 'ride started',
            "fare" : float(data['fare']),
            "created_at" : datetime.now().isoformat(),
            "role": 'communication'
            }
        publish_message('communication',data)

        return jsonify({'message':'okkk'})

    @app.route('/checkride',methods = ["POST"])
    def checkride():
        data = request.get_json()
        ride = Ride.query.filter(
            Ride.user_id == data['userid'],
            Ride.status.in_(['ride started', 'driver arrived'])
        ).first()
        if ride:
            return jsonify({'message':'ridestarted','rideid':ride.id})
        return jsonify({'message':'okkk'})  

    @app.route('/getride', methods = ['POST'])
    def getride():
        data = request.get_json()
        driver = Driver.query.filter_by( email = data['email']).first()
        ride = Ride.query.filter(
            Ride.driver_id == driver.id,
            Ride.status.in_(['ride started', 'driver arrived', 'trip started'])
        ).first()
        user = User.query.filter_by(user_id = ride.user_id).first()
        rides = {
            'id':ride.id,
            'vehicle_type':ride.vehicle_type,
            'current_location':ride.current_location,
            'pick_up_location':ride.pick_up_location,
            'drop_location':ride.drop_location,
            'pickupkm':ride.pickup_km,
            'total_km':ride.total_km,
            'fare':ride.fare,
            'phone':user.phone
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
            'fare':ride.fare + 30
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
            'fare':ride.fare + 30,
            'live':{'lat':live.latitude,'lng':live.longitude},
            'phone':driver.phone,
            'ride_id':ride.id,
            'payment_status': ride.payment_status if ride.payment_status is not None else 'pending'
        }
        return jsonify({'message':'okkk','ride':rides})

    @app.route('/ispayed', methods = ["POST"])
    def ispayed():
        try:
            data = request.get_json()
            ride = Ride.query.filter_by(id = data['rideid']).first()
            if ride.payment_status == 'payment done':
                return jsonify({'message':'payment done'})
        except:
            return jsonify({'message':'not done'})
        
    @app.route('/paymentconfirm', methods = ["POST"])
    def paymentconfirm():
        try:
            data = request.get_json()
            print('entered')
            ride = Ride.query.filter_by(id = data['rideid']).first()
            print(ride)
            ride.status = 'trip completed'
            ride.payment_status = 'payment done'
            ride.payment_type = 'cash'
            db.session.commit()
            return jsonify({'message':'ok','driverid':ride.driver_id})
        except Exception as e:
            print(e)
            return jsonify({'message':'notok'})

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
        try:
            ride = Ride.query.filter_by(id = data['rideid']).first()
            user = User.query.filter_by(user_id = ride.user_id).first()
            ride.status = 'driver arrived'
            db.session.commit()
            otp = generate_otp()
            # send_mail(user.email,user.fullname,otp)
            return jsonify({'message':'ok','otp':otp})
        except:
            return jsonify({'message':'error'})
    
    @app.route('/tripstarted',methods = ["POST"])
    def tripstarted():
        data = request.get_json()
        try:
            driver = Driver.query.filter_by(email = data['email']).first()
            ride = Ride.query.filter(
                Ride.driver_id == driver.id,
                Ride.status == 'driver arrived'
            ).first()
            ride.status = 'trip started'
            db.session.commit()
            return jsonify({'message':'ok'})
        except:
            return jsonify({'message':'error'})
        
    @app.route('/istripstarted',methods = ['POST'])
    def istripstarted():
        data = request.get_json()
        try:
            try:
                user = User.query.filter_by(email = data['email']).first()
                ride = Ride.query.filter(Ride.id == data['rideid'], Ride.user_id == user.id, Ride.status == 'cancelled by driver').first()
                if ride:
                    data = {
                        'rideid':ride.id
                    }
                    publish_message('communication',{'userid':ride.user_id,'driverid':ride.driver_id,'role':'cancelled by driver'})
                    return jsonify({'message':'driver is cancelled'})
            except:
                pass
            user = User.query.filter_by(email = data['email']).first()
            ride = Ride.query.filter(
                Ride.id == data['rideid'],
                Ride.user_id == user.id,
                Ride.status == 'trip started'
            ).first()     
            if ride:
                return jsonify({'message':'trip started'})
            return jsonify({'message':'ok'})
        except:
            return jsonify({'message':'error'})

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
    
    @app.route('/getpayment', methods = ["POST"])
    def getpayment():
        data = request.get_json()
        print(data)
        ride = Ride.query.filter_by(id = data['rideid']).first()
        print(ride)
        if ride.payment_status == 'paid':
            return jsonify({'message':'payment done'})
        return jsonify({'message':'ok'})
    
    @app.route('/paymentdone', methods = ["POST"])
    def paymentdone():
        data = request.get_json()
        ride = Ride.query.filter_by(id = data['rideid']).first()
        ride.payment_status = 'paid'
        ride.payment_type = 'online'
        db.session.commit()
        return jsonify({'message':'ok'})

    @app.route('/isridefinish', methods = ["POST"])
    def isridefinish(): 
        data = request.get_json()
        print(data)
        try:
            ride = Ride.query.filter(Ride.status == 'trip completed', Ride.id == data['rideid']).first()
            if ride:
                return jsonify({'message':'trip completed'})
            print('lsdjflaskdjf')
            return jsonify({'message':'ok'})
        except:
            return jsonify({'message':'error'})
    
    @app.route('/ridefinish',methods = ['POST'])
    def ridefinish():
        try:
            data = request.get_json()
            ride = Ride.query.filter_by(id = data['rideid']).first()
            ride.status = 'trip completed'
            db.session.commit()
            return jsonify({'message':'ok'})
        except:
            return jsonify({'message':'error'})

    @app.route('/cancelfromdriver', methods = ["POST"])
    def cancelfromdriver():
        data =  request.get_json()
        try:
            ride = Ride.query.filter_by(id = data['rideid']).first()
            ride.status = 'cancelled by driver'
            cancel = CancelReason(ride_id = ride.id, reason = data['reason'])
            db.session.add(cancel)
            db.session.commit()
            return jsonify({'message':'ok'})  
        except Exception as e:
            print('something error',e)
            return jsonify({'message':'error'})
        
    @app.route('/cancelfromuser', methods = ["POST"])
    def cancelfromuser():
        data = request.get_json()
        try:
            ride = Ride.query.filter_by(id=data['rideid']).first()
            ride.status = 'cancelled by user'
            cancel = CancelReason(ride_id = ride.id, reason = data['reason'])
            db.session.add(cancel)
            db.session.commit()
            return jsonify({'message':'ok'})
        except:
            return jsonify({'message':'ride not found'})

    @app.route('/checkusercancelled', methods = ["POST"])
    def checkusercancelled():
        data = request.get_json()
        ride = Ride.query.filter_by(id = data['rideid']).first()
        if ride.status == 'cancelled by user':
            return jsonify({'message':'cancelled'})
        return jsonify({'message':'ok'})

    @app.route('/fetchride', methods = ["GET"])
    def fetchride():
        rides = Ride.query.all()
        ridelist = [{'id':ride.id, 'userid':ride.user_id, 'driverid':ride.driver_id, 'vehicle':ride.vehicle_type, 'pickup':ride.pick_up_location, 'drop':ride.drop_location, 'km':ride.total_km, 'status':ride.status, 'fare':ride.fare, 'date':ride.created_at} for ride in rides]
        return jsonify(ridelist)

    @app.route('/fetchlive', methods = ["GET"])
    def fetchlive():
        lives = Liveloc.query.all()
        livelocations = [{'id':live.id, 'driver':live.driver_id, 'lat':live.latitude, 'lng':live.longitude} for live in lives if live.latitude is not None]
        print(livelocations)

        return jsonify(livelocations)
    
    @app.route('/monthly_fares/<int:year>', methods=['GET'])
    def get_monthly_fares(year):

        results = (
            db.session.query(
                extract('month', Ride.created_at).label('month'),
                func.sum(Ride.fare).label('total_fare')
            )
            .filter(extract('year', Ride.created_at) == year,
            Ride.status == 'trip completed'
            )
            .group_by(extract('month', Ride.created_at))
            .order_by(extract('month', Ride.created_at))
            .all()
        )
        
        month_names = [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        ]
        
        monthly_fares_dict = {i + 1: {'month': month_names[i], 'value': 0} for i in range(12)}

        
        for month, total_fare in results:
            monthly_fares_dict[month]['value'] = float(total_fare) if total_fare is not None else 0
        
        monthly_fares = list(monthly_fares_dict.values())
        
        return jsonify(monthly_fares)

    def get_last_monday(date):
        days_since_monday = (date.weekday() - 0) % 7 
        last_monday = date - timedelta(days=days_since_monday)
        return last_monday
    
    def get_next_sunday(dt):
        days_until_sunday = (6 - dt.weekday()) % 7 
        next_sunday = dt + timedelta(days=days_until_sunday)
        return next_sunday
    
    @app.route('/get_weekly_data', methods = ['GET'])
    def weekly_fares():
        session = db.session
        try:
            now = datetime.now()
            start_of_week = get_last_monday(now)
            end_of_week = get_next_sunday(now)
            print(get_last_monday(now),'kfihksdgsdkjfg')
            results = Ride.query.filter(
                    func.date(Ride.created_at) >= func.date(start_of_week),
                    func.date(Ride.created_at) <= func.date(end_of_week)
                ).all()
            print(results)
            data = [
                {'day': 'Monday', 'completed': 0, 'cancelled': 0},
                {'day': 'Tuesday', 'completed': 0, 'cancelled': 0},
                {'day': 'Wednesday', 'completed': 0, 'cancelled': 0},
                {'day': 'Thursday', 'completed': 0, 'cancelled': 0},
                {'day': 'Friday', 'completed': 0, 'cancelled': 0},
                {'day': 'Saturday', 'completed': 0, 'cancelled': 0},
                {'day': 'Sunday', 'completed': 0, 'cancelled': 0},
            ]

            for result in results:
                day_of_week = calendar.day_name[result.created_at.weekday()]
                for entry in data:
                    if entry['day'] == day_of_week:
                        entry['completed'] += float(result.fare) if result.status == 'trip completed' else 0
                        entry['cancelled'] += float(result.fare) if result.status == 'cancelled by user' or result.status == 'cancelled by driver' else 0
                        break

            week_abbreviations = {
                'Sunday': 'SUN',
                'Monday': 'MON',
                'Tuesday': 'TUE',
                'Wednesday': 'WED',
                'Thursday': 'THU',
                'Friday': 'FRI',
                'Saturday': 'SAT'
            }

            for entry in data:
                entry['day'] = week_abbreviations[entry['day']]
            print(data)
            return jsonify({'message': data})
        except Exception as e:
            print(e)
            return jsonify({'error': str(e)}), 500
        
    def date_only(datetime_str):
        date_object = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        date_only = date_object.date()

        return date_only

    @app.route('/dailyprofit', methods = ["GET"])
    def dailyprofit():
        today = date.today()   
        print(today) 
        ride = Ride.query.filter_by(status='trip completed').filter(func.date(Ride.created_at) == today).all()
        accepted = Ride.query.filter(Ride.status == 'trip completed').all()
        cancelled = Ride.query.filter(Ride.status != 'trip completed').all()
        ride2 = Ride.query.filter_by(status = 'trip completed').all()
        total = 0
        for i in ride2:
            total += i.fare

        return jsonify({'message':len(ride)*30, 'cancelled':len(cancelled), 'accepted': len(accepted), 'total':total, 'total_profit':len(ride2)*30})
    
    def get_day_name(date_obj):
        try:
            if not isinstance(date_obj, datetime):
                raise ValueError("The input must be a datetime object.")
            
            day_name = date_obj.strftime('%A')
            
            return day_name
        except ValueError:
            return "Invalid date format"    
    
    @app.route('/weeklyearnings', methods = ['POST'])
    def weeklyearnings():
        data = request.get_json()
        today = date.today()
        driver = Driver.query.filter_by(email = data['email']).first()
        ride = Ride.query.filter(Ride.driver_id == driver.driver_id, Ride.status == 'trip completed', Ride.created_at >= get_last_monday(today)).all()
        ride2 = Ride.query.filter(
                Ride.driver_id == driver.driver_id,
                Ride.status == 'trip completed',
                func.date(Ride.created_at) == today
            ).all()
        total = 0
        today = 0
        data = {'Sunday': [],'Monday': [],'Tuesday': [],'Wednesday': [],'Thursday': [],'Friday': [],'Saturday': []}
        for i in ride:
            if get_day_name(i.created_at) in data:
                data[get_day_name(i.created_at)].append({'location':i.drop_location, 'fare':i.fare, 'date':i.created_at})
            total += i.fare
        for i in ride2:
            today += i.fare
        print(data)
        return jsonify({'message':total,'today':today,'data':data})
    
    @app.route('/gettripuser', methods = ["POST"])
    def gettripuser():
        data = request.get_json()
        user = User.query.filter_by(email = data['email']).first()
        ride = Ride.query.filter_by(user_id = user.user_id).all()
        data = []
        for i in ride:
            driver = Driver.query.filter_by(driver_id = i.driver_id).first()
            data.append({
            'id': i.id,
            'driver_name': driver.fullname,
            'vehicle': i.vehicle_type,
            'pickup': i.pick_up_location,
            'drop': i.drop_location,
            'km': i.total_km,
            'fare': i.fare,
            'date': i.created_at.strftime('%Y-%m-%d')
            })
        print(data)
        return jsonify({'data':data})

    @app.route('/getdata', methods = ["POST"])
    def getdata():
        data = request.get_json()
        salary_payment = Ride.query.filter(Ride.driver_id == data['driver_id'], Ride.status == 'trip completed').all()
        salary_info = [{'id':i.id, 'vehicle':i.vehicle_type.title(), 'drop':i.drop_location.title(), 'km':i.total_km, 'payment_type':i.payment_type.title(), 'fare':i.fare, 'date':i.created_at, 'salary_status':i.salary_status}for i in salary_payment]
        deduction = 0
        for j in salary_payment:
            if j.payment_type == 'cash' and j.salary_status is None:
                deduction+=30
        salary_info.append(deduction)
        print(salary_info)
        return jsonify(salary_info)
    
    @app.route('/sendsalary', methods = ['POST'])
    def sendsalary():
        try:
            data = request.get_json()
            print(data)
            formatted_date = datetime.strptime(data['date'], '%a, %d %b %Y %H:%M:%S %Z')
            print(formatted_date)
            wallet = Wallet(driver_id = data['driverid'], ride_id = data['rideid'],date = formatted_date, amount = Decimal(data['fare']))
            ride = Ride.query.filter_by(id = data['rideid']).first()
            ride.salary_status = 'credited'
            db.session.add(wallet)
            db.session.commit()
            return jsonify({'message':'success'})
        except:
            return jsonify({'message':'error'})
    
    @app.route('/deductamount', methods = ["POST"])
    def deductamount():
        try:
            data = request.get_json()
            formatted_date = datetime.strptime(data['date'], '%a, %d %b %Y %H:%M:%S %Z')
            print(formatted_date)
            wallet = Wallet.query.filter(Wallet.driver_id == data['driverid'], Wallet.amount > 30).first()
            ride = Ride.query.filter_by(id = data['rideid']).first()
            wallet.amount -= 30
            ride.salary_status = 'deducted'
            db.session.commit()
            return jsonify({'message':'success'})
        except:
            return jsonify({'message':'error'})
        
    @app.route('/getrides', methods = ['POST'])
    def getrides():
        data = request.get_json()
        driver = Driver.query.filter_by(email = data['email']).first()
        ride = Ride.query.filter(Ride.driver_id == driver.id, Ride.status == 'trip completed').all()
        data = [{'id':i.id, 'amount':i.fare}for i in ride]
        return jsonify({'message':ride})
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=9640)