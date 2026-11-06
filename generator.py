import argparse

from fpdf import FPDF
import cv2 as cv
import json

width = 11 * 72
height = 8.5 * 72

one_width = width / 3

def move_tags(tags):
    if tags[3] < 49:
        tags[3] += 1
    elif tags[2] < 48:
        tags[2] += 1
    elif tags[1] < 47:
        tags[1] += 1
    else:
        tags[0] += 1
        tags[1] = tags[0] + 1
        tags[2] = tags[1] + 1
        tags[3] = tags[2] + 1
    return tags

def main():
    parser = argparse.ArgumentParser(prog="Ballot Generator", description="Generates ballots that can be scanned by the PORG ballot scanner")
    parser.add_argument("input", help="input json file to be parsed", required=True)
    parser.add_argument("output", help="Name of file to be generated", required=True)
    parser.add_argument("count", help="Number of pages to be generated, three to a page", required=False, type=int, default=1)
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

    dictionary = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_5X5_50)
    tag_ids = [0, 1, 2, 3]

    tag = cv.aruco.generateImageMarker(dictionary, 0, 36)
    retval, bfr = cv.imencode('.png', tag)
    bytes = bfr.tobytes()
    pdf = FPDF(unit='pt', format='letter', orientation='landscape')

    pdf.set_auto_page_break(False)
    for question in ballot['questions']:
        pass


    pdf.add_page()
    for i in range(3):
        x_offset = one_width * i
        pdf.image(bytes, x=18+x_offset, y=18, w=36, h=36)
        pdf.image(bytes, x=one_width-18+x_offset-36, y=18, w=36, h=36)
        pdf.image(bytes, x=18+x_offset, y=height-36-18, w=36, h=36)
        pdf.image(bytes, x=one_width-18+x_offset-36, y=height-18-36, w=36, h=36)

    pdf.output("test.pdf")

if __name__ == '__main__':
    main()