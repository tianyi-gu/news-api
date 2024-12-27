from transformers import AutoTokenizer, AutoModel
import os

def download_models():
    model_name = "distilbert-base-uncased-distilled-squad"
    model_dir = "./models"
    
    print(f"Downloading {model_name}...")
    
    # Create models directory if it doesn't exist
    os.makedirs(model_dir, exist_ok=True)
    
    # Download tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    
    # Save locally
    tokenizer.save_pretrained(os.path.join(model_dir, model_name))
    model.save_pretrained(os.path.join(model_dir, model_name))
    
    print("Models downloaded successfully!")

if __name__ == "__main__":
    download_models()