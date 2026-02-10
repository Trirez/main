"""Test all captcha generators"""
from captcha_generators.text_captcha import TextCaptcha
from captcha_generators.image_captcha import ImageCaptcha
from captcha_generators.cloudflare_captcha import CloudflareCaptcha
from captcha_generators.puzzle_captcha import PuzzleCaptcha

print('Testing TextCaptcha...')
tc = TextCaptcha()
result = tc.generate()
print(f'  Text length: {len(result["text"])}, Image generated: {len(result["image"]) > 100}')

print('Testing ImageCaptcha...')
ic = ImageCaptcha()
result = ic.generate()
print(f'  Prompt: {result["prompt"][:30]}..., Images: {len(result["images"])}')

print('Testing CloudflareCaptcha...')
cc = CloudflareCaptcha()
result = cc.generate()
print(f'  Challenge ID: {result["challenge_id"][:16]}...')

print('Testing PuzzleCaptcha (sliding)...')
pc = PuzzleCaptcha()
result = pc.generate_sliding_puzzle()
print(f'  Correct X: {result["correct_x"]}, Piece Y: {result["piece_y"]}')

print('Testing PuzzleCaptcha (drag)...')
result = pc.generate_drag_puzzle()
print(f'  Pieces: {len(result["pieces"])}, Positions: {len(result["positions"])}')

print('ALL TESTS PASSED!')
