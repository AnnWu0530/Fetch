import datetime
import logging
import json
from confluent_kafka import Consumer, Producer, KafkaError

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define the Kafka consumer configuration
consumer_config = {
    'bootstrap.servers': 'kafka:29092',  
    'group.id': 'my-consumer-group',  # Consumer group ID
    'auto.offset.reset': 'earliest',  # Start reading from the beginning of the topic
}

# Define the Kafka producer configuration
producer_config = {
    'bootstrap.servers': 'kafka:9092',  
}
# Create Kafka consumer and producer instances
consumer = Consumer(consumer_config)
producer = Producer(producer_config)

# Subscribe to the input Kafka topic
consumer.subscribe(['user-login'])
output_topic = 'login_record'
# Define a function to transform the data
def transform_data(data):
    try:
        data_dict = json.loads(data)

         # Convert the timestamp to a datetime format
        timestamp = int(data_dict.get("timestamp"))
        if timestamp:
            # Convert to datetime (assuming UTC timezone)
            datetime_obj = datetime.utcfromtimestamp(timestamp)
            data_dict['datetime'] = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
    
        # Convert the transformed data back to JSON
        transformed_data = json.dumps(data_dict)
        print(transformed_data)
        return transformed_data
    except json.JSONDecodeError as e:
        print(f'JSON decoding error: {e}')
        return None
    

# Define a function to generate insights
def generate_insights(data):
    try:
        data_dict = transform_data(data)
        
        # Check if the event is a login event based on the "device_type" field
        device_type = data_dict.get("device_type")
        if device_type and device_type.lower() == "login":
            # Generate insights based on device type
            insight = f"Login from {device_type} device"
            return insight
        
        return None  
        
    except json.JSONDecodeError as e:
        print(f'JSON decoding error: {e}')
        return None

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                logging.info('Reached end of partition')
            else:
                logging.error('Kafka error: %s', msg.error())
        else:
            # Process the received message
            data = msg.value().decode('utf-8')

            # Transform the data
            transformed_data = transform_data(data)

            if transformed_data:
                logging.info('Transformed data: %s', transformed_data)

                # Produce the transformed data to the output Kafka topic
                producer.produce(output_topic, key=None, value=transformed_data)

                # Generate insights
                insight = generate_insights(transformed_data)
                if insight:
                    logging.info('Insight: %s', insight)

except KeyboardInterrupt:
    pass
finally:
    # Close the Kafka consumer and producer gracefully
    consumer.close()
    producer.flush()
