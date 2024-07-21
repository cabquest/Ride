
import pika
import json
from models import User, Driver, db
from app import create_app

app = create_app()
app.app_context().push()

rabbitmq_host = 'localhost'  
rabbitmq_port = 5672
rabbitmq_user = 'guest'  
rabbitmq_password = 'guest'  
rabbitmq_queue = 'ride'

def get_rabbitmq_connection():
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
    parameters = pika.ConnectionParameters(rabbitmq_host,
                                           rabbitmq_port,
                                           '/',
                                           credentials)
    return pika.BlockingConnection(parameters)


def callback(ch, method, properties, body):
    print(f"Received {body}")
    data = json.loads(body)
    print(data)
    if data['role'] == 'user':
        user = User(user_id=data['id'], fullname=data['fullname'], email=data['email'], phone=data['phone'])
        db.session.add(user)
        db.session.commit()
    elif data['role'] == 'driver':
        user = Driver(driver_id=data['id'], fullname=data['fullname'], email=data['email'], phone=data['phone'])
        db.session.add(user)
        db.session.commit()
    print("Processing done")

def start_consumer():
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()

        channel.queue_declare(queue=rabbitmq_queue)

        channel.basic_consume(queue=rabbitmq_queue, on_message_callback=callback, auto_ack=True)

        print('Consumer started. Waiting for messages...')
        channel.start_consuming()

    except Exception as e:
        print(f'Error in consumer: {str(e)}')

if __name__ == '__main__':
    start_consumer()