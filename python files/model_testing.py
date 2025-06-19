from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

# Step 1: Load base BioGPT
base_model = AutoModelForCausalLM.from_pretrained("microsoft/biogpt")

# Step 2: Load tokenizer from your fine-tuned repo
tokenizer = AutoTokenizer.from_pretrained("santanukumar07/biogpt-finetune")

# Step 3: Attach LoRA adapter
model = PeftModel.from_pretrained(base_model, "santanukumar07/biogpt-finetune")

input_text = "Patient Case: headache, nausea, age:30\nTreatment Recommendation:"

inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
model.eval()

with torch.no_grad():
    output = model.generate(
        **inputs,
        max_new_tokens=50,
        temperature=0.7,
        top_p=0.9
    )

print(tokenizer.decode(output[0], skip_special_tokens=True))
