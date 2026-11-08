import math

import cv2 as cv
import numpy as np
from cv2 import Mat
import argparse
import json


def extract_votes(img: Mat, ballot_info: dict):
    box_width = 9
    extract = {}
    for question in ballot_info:
        extract[question] = None
        if "text" in question:
            pass
        else:
            vals = []
            for ans in ballot_info[question]["pos"]:
                coords = ballot_info[question]["pos"][ans]
                box = img[int(coords[0]):int(coords[0] + box_width), int(coords[1]):int(coords[1] + box_width)]
                cv.imwrite(f"test_box_{question}_{ans}.png", box)


def main():
    parser = argparse.ArgumentParser(description='Program to extract and upload votes on PORG ballots')
    parser.add_argument("input", help="json file that describes what to scan on the ballot")
    parser.add_argument("--camera", "-c", type=int, default=0, const=0, nargs='?', help="Specify which camera to use")
    parser.add_argument("--upload", "-u", help="If the ballots should be uploaded to the website", action=argparse.BooleanOptionalAction)
    parser.add_argument("--output", "-o", type=str, required=False, nargs='?', help="The optional file of which to output the results to")
    args = parser.parse_args()

    ballot_info = {}
    with open(args.input, "r") as f:
        try:
            ballot_info = json.load(f)
        except json.decoder.JSONDecodeError:
            print("Invalid json file provided")
            exit(1)

    cap = cv.VideoCapture(args.camera)
    if not cap.isOpened():
        print("Coudln't open camera")
        exit(1)

    seen_ballots = set()

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        detector = cv.aruco.ArucoDetector(cv.aruco.getPredefinedDictionary(cv.aruco.DICT_5X5_50), cv.aruco.DetectorParameters())
        corners, ids, rejects = detector.detectMarkers(frame)

        frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

        cv.imshow('frame', frame)
        if not ids is None and len(ids) == 4:
            id_order = ids.copy().tolist()
            ids.sort()
            if tuple(id_order) in seen_ballots:
                continue
            else:
                seen_ballots.add(tuple(id_order))
            points = []
            id_count = 0
            for id in ids:
                corner = corners[id_order.index(id)]
                point_to_get = id_count
                if point_to_get == 1:
                    point_to_get = 3
                elif point_to_get == 3:
                    point_to_get = 1
                points.append(corner[0][point_to_get].tolist())
                id_count += 1
            # https://theailearner.com/2020/11/06/perspective-transformation/
            width_ad = np.sqrt(((points[0][0] - points[3][0]) ** 2 + (points[0][1] - points[3][1]) ** 2))
            width_bc = np.sqrt(((points[1][0] - points[2][0]) ** 2 + (points[1][1] - points[2][1]) ** 2))
            max_width = max(width_ad, width_bc)
            height_ab = np.sqrt(((points[0][0] - points[1][0]) ** 2 + (points[0][1] - points[1][1]) ** 2))
            height_cd = np.sqrt(((points[2][0] - points[3][0]) ** 2 + (points[2][1] - points[3][1]) ** 2))
            max_height = max(height_ab, height_cd)
            input_pts = np.float32(points)
            output_pts = np.float32([[0, 0], [0, max_height - 1], [max_width - 1, max_height - 1], [max_width - 1, 0]])
            transform = cv.getPerspectiveTransform(input_pts, output_pts)
            # we want to be 224 by 540
            warped = cv.warpPerspective(frame, transform, (int(max_width), int(max_height)), flags=cv.INTER_LINEAR)
            warped = cv.resize(warped, (224, 540))
            cv.imshow('warped', warped)
            cv.imwrite("test_ballot.png", warped)

            extract_votes(warped, ballot_info)



        if cv.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv.destroyAllWindows()

if __name__ == '__main__':
    main()

