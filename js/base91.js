/**
 * Base91 encoding/decoding implementation
 */
class Base91 {
    constructor() {
        this.alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!#$%&()*+,./:;<=>?@[]^_`{|}~"';
        this.decode_table = {};
        for (let i = 0; i < this.alphabet.length; i++) {
            this.decode_table[this.alphabet[i]] = i;
        }
    }
    
    encode(data) {
        let v = 0, b = 0, n = 0;
        let output = '';
        
        for (let i = 0; i < data.length; i++) {
            b = (b << 8) | (data[i] & 0xff);
            n += 8;
            
            while (n >= 13) {
                v = b >>> (n - 13);
                output += this.alphabet[Math.floor(v / 91)] + this.alphabet[v % 91];
                n -= 13;
                b &= ~(v << n);
            }
        }
        
        if (n > 0) {
            output += this.alphabet[Math.floor(b / 91)];
            if (n > 7 || b % 91 > 0) {
                output += this.alphabet[b % 91];
            }
        }
        
        return output;
    }
    
    decode(str) {
        let v = -1, b = 0, n = 0;
        const output = [];
        
        for (let i = 0; i < str.length; i++) {
            const c = str[i];
            if (!(c in this.decode_table)) continue;
            
            const cVal = this.decode_table[c];
            if (v < 0) {
                v = cVal;
            } else {
                v += cVal * 91;
                b |= v << n;
                n += (v & 8191) > 88 ? 13 : 14;
                
                do {
                    output.push(b & 0xff);
                    b >>>= 8;
                    n -= 8;
                } while (n > 7);
                
                v = -1;
            }
        }
        
        if (v + 1) {
            output.push((b | v << n) & 0xff);
        }
        
        return new Uint8Array(output);
    }
}

// Export for Node.js/CommonJS
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Base91;
}
