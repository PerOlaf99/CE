import numpy as np
import tensorflow as tf
import pickle
from utils import read_rsd, preprocess_traces

# Load the trained model
model = tf.keras.models.load_model('final_basecaller_model.h5', custom_objects={'ctc_loss': None})  # we don't need loss for inference

# Load char mapping
with open('char_map.pkl', 'rb') as f:
    char_to_idx = pickle.load(f)
idx_to_char = {v: k for k, v in char_to_idx.items()}

def ctc_decode(predictions, beam_width=10):
    """Decode using CTC beam search (or greedy)."""
    # predictions: (1, time, num_classes)
    # Greedy decoding (simpler)
    pred_indices = np.argmax(predictions, axis=-1)[0]  # (time,)
    # Remove consecutive duplicates and blanks (blank index = 0)
    prev = -1
    seq = []
    for idx in pred_indices:
        if idx != prev and idx != 0:  # 0 is blank
            seq.append(idx_to_char.get(idx, 'N'))
        prev = idx
    return ''.join(seq)

def call_bases(traces):
    """Preprocess traces and run the model."""
    data = preprocess_traces(traces)
    data = np.expand_dims(data, axis=0)  # (1, T, 4)
    pred = model.predict(data, verbose=0)
    seq = ctc_decode(pred)
    # Compute quality scores from softmax probabilities
    probs = np.max(pred[0], axis=-1)  # (T,)
    # For each called base, get its probability from the position where it was called (simplified)
    # We'll just assign average quality per base
    qv = -10 * np.log10(1 - np.mean(probs) + 1e-10)
    qualities = [int(qv)] * len(seq)
    return seq, qualities

def basecall_rsd(filepath, output_fasta=None, output_fastq=None):
    traces = read_rsd(filepath)
    seq, quals = call_bases(traces)
    base = os.path.basename(filepath).replace('.rsd', '')
    if output_fasta:
        with open(output_fasta, 'w') as f:
            f.write(f">{base}\n{seq}\n")
    if output_fastq:
        with open(output_fastq, 'w') as f:
            f.write(f"@{base}\n{seq}\n+\n")
            f.write(''.join(chr(q+33) for q in quals) + "\n")
    return seq, quals

if __name__ == "__main__":
    import sys
    input_rsd = sys.argv[1]
    basecall_rsd(input_rsd, output_fasta="result.fasta", output_fastq="result.fastq")