from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline 

import torch 

 

# Small enough to run on CPU; better on GPU if available 

MODEL_ID = 'microsoft/Phi-3.5-mini-instruct' 

 

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID) 

model = AutoModelForCausalLM.from_pretrained( 

    MODEL_ID, 

    torch_dtype=torch.float32,   # use float16 if GPU available 

    device_map='auto')           # CPU or GPU automatically 

 

pipe = pipeline('text-generation', model=model, tokenizer=tokenizer, 

                max_new_tokens=512) 

print(pipe('Summarise: ...')[0]['generated_text'])

from langchain_huggingface import HuggingFacePipeline 

 

llm = HuggingFacePipeline(pipeline=pipe) 

# Now use the same .invoke() interface as Gemini 
