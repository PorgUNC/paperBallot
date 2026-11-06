import cv2 as cv
import numpy as np

def main():
    cap = cv.VideoCapture(0)
    if not cap.isOpened():
        exit(1)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        detector = cv.aruco.ArucoDetector(cv.aruco.getPredefinedDictionary(cv.aruco.DICT_5X5_50), cv.aruco.DetectorParameters())
        corners, ids, rejects = detector.detectMarkers(frame)

        cv.imshow('frame', cv.aruco.drawDetectedMarkers(frame, corners, ids))
        if not ids is None and len(ids) == 4:
            id_order = ids.copy().tolist()
            ids.sort()
            points = []
            for id in ids:
                corner = corners[id_order.index(id)]
                points.append(corner[0][0].tolist())
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
            warped = cv.warpPerspective(frame, transform, (int(max_width), int(max_height)), flags=cv.INTER_LINEAR)
            cv.imshow('warped', warped)


        if cv.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv.destroyAllWindows()

if __name__ == '__main__':
    main()

