import argparse
import random

import fpdf
from fpdf import FPDF
import cv2 as cv
import json

from fpdf.enums import MethodReturnValue

inch = 72
width = 11 * inch
height = 8.5 * inch

one_width = int(width / 3)

def generate_tag(used):
    while True:
        tag = tuple(sorted(random.sample(range(50), 4)))
        if not tag in used: break
    used.add(tag)
    return tag

def get_tag_bytes(id):
    dictionary = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_5X5_50)
    tag = cv.aruco.generateImageMarker(dictionary, id, 36)
    retval, bfr = cv.imencode('.png', tag)
    return bfr.tobytes()

def main():
    parser = argparse.ArgumentParser(prog="Ballot Generator", description="Generates ballots that can be scanned by the PORG ballot scanner")
    parser.add_argument("input", help="input json file to be parsed")
    parser.add_argument("output", help="Name of file to be generated")
    parser.add_argument("--count", "-c", help="Number of pages to be generated, three to a page", required=False, type=int, default=1)
    parser.add_argument("--flavor-text", "-f", help="Text to be added to the top of the ballot, i.e. instructions", required=False, type=str, default="Thank you for your response! Please respond by completely filling the one box that best describes your answer. For open response, just make sure to write within the box!")
    args = parser.parse_args()

    if args.count < 1:
        print("You can't generate no pages you idiot")
        exit(1)

    try:
        with open(args.input) as json_file:
            ballot = json.load(json_file)
    except FileNotFoundError:
        print("File not found")
        exit(1)
    except json.decoder.JSONDecodeError:
        print("Invalid json file")
        exit(1)


    used_tags = set()

    pdf = FPDF(unit='pt', format='letter', orientation='landscape')
    pdf.set_font("Helvetica", size=9)

    pdf.set_auto_page_break(False)

    for i in range(args.count):
        pdf.add_page()
        for i in range(3):
            x_offset = one_width * i

            # Add aruco tags to corners
            tag_ids = generate_tag(used_tags)

            pdf.image(get_tag_bytes(tag_ids[0]), x=18+x_offset, y=18, w=36, h=36)
            pdf.image(get_tag_bytes(tag_ids[1]), x=one_width-18+x_offset-36, y=18, w=36, h=36)
            pdf.image(get_tag_bytes(tag_ids[2]), x=18+x_offset, y=height-36-18, w=36, h=36)
            pdf.image(get_tag_bytes(tag_ids[3]), x=one_width-18+x_offset-36, y=height-18-36, w=36, h=36)

            # Add logo
            logo_size = (3/4)*inch
            pdf.image("./resources/logo.png", x=(one_width/2)-(logo_size/2)+x_offset, y=18, w=logo_size, h=logo_size)

            running_y = 18+logo_size

            pdf.set_xy(x_offset+18, running_y+6)
            running_y += 6
            running_y += pdf.multi_cell(w=one_width-36, text=args.flavor_text, align=fpdf.Align.C, output=MethodReturnValue.HEIGHT)

            pdf.line(x1=18+x_offset, y1=running_y+3, x2=one_width-18+x_offset, y2=running_y+3)

            answer_positions = {}

            # Questions
            q_count = 1
            for question in ballot['questions']:
                pdf.set_xy(x_offset+18, running_y+6)
                running_y += 6
                running_y += pdf.multi_cell(w=one_width-36, text=f"{q_count}. {question["q"]}", output=MethodReturnValue.HEIGHT)
                answer_positions[question["q"]] = {}

                if "text" in question:
                    # Text box answer
                    pdf.rect(x=18+x_offset, y=running_y + 6, w=one_width-36, h=36)
                    answer_positions[question["q"]]["text"] = True
                    answer_positions[question["q"]]["pos"] = [0, running_y+6 - 18, one_width-36, running_y+6+36 - 18]
                    running_y += 6 + 36
                else:
                    # multiple choice
                    answer_positions[question["q"]]["pos"] = {}
                    q_offset = 0
                    col_count = 1
                    for option in question['options']:

                        pdf.rect(x=18+6+x_offset+q_offset, y=running_y+3, w=9, h=9)
                        answer_positions[question["q"]]["pos"][option] = [6+q_offset, running_y+3 - 18]
                        pdf.set_xy(x_offset+q_offset+18+6+10+3, running_y+3)
                        if "col" in question and col_count <= question["col"]:
                            s_length = pdf.get_string_width(option) + 9
                            out_height = pdf.multi_cell(w=s_length, text=option, output=MethodReturnValue.HEIGHT)
                            if col_count == question["col"]:
                                col_count = 1
                                q_offset = 0
                                running_y += out_height + 3
                            else:
                                q_offset += s_length + 9 + 6
                                # If it doesnt end perfectly on a column make sure to increase height
                                if question["options"].index(option) == len(question["options"]) - 1:
                                    running_y += 3 + out_height
                                col_count += 1
                        else:
                            running_y += 3
                            running_y += pdf.multi_cell(w=one_width-36-6-3, text=option, output=MethodReturnValue.HEIGHT)


                q_count += 1


    pdf.output(f"{args.output}.pdf")
    with open(f"{args.output}.json", "w") as f:
        f.write(json.dumps(answer_positions))
        f.close()

if __name__ == '__main__':
    main()