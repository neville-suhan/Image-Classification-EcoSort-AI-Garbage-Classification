from tensorflow.keras.preprocessing import image
import numpy as np

def predict_image(model, image_path, class_names, target_size=(224, 224)):
    # """
    # Predict image using MobileNetV2 model
    # """

    # Load image
    img = image.load_img(image_path, target_size=target_size)

    # Convert to array
    img_array = image.img_to_array(img)

    # Normalize (IMPORTANT for MobileNet)
    img_array = img_array / 255.0

    # Expand dims
    img_array = np.expand_dims(img_array, axis=0)

    # Prediction
    predictions = model.predict(img_array)

    # Get index
    predicted_index = np.argmax(predictions[0])

    confidence = predictions[0][predicted_index]

    predicted_class = class_names[predicted_index]

    # 🔥 HANDLE BIOLOGICAL = ORGANIC
    if predicted_class == "biological":
        predicted_class = "organic"

    return predicted_class, confidence