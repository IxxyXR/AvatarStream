# Pose HTTP API Contract

This document defines the JSON returned by the local tracker listener.

## Endpoint

- `GET http://127.0.0.1:40094/pose`
- Health check: `GET http://127.0.0.1:40094/health`

## Success Response (`/pose`)

Status: `200 OK`

```json
{
  "ok": true,
  "updated_ms": 1772190000123,
  "pose": {
    "timestamp_ms": 1772190000101,
    "landmarks": {
      "nose": { "x": 0.451, "y": 0.307, "z": -0.256, "visibility": 0.997 },
      "left_shoulder": { "x": 0.52, "y": 0.41, "z": -0.11, "visibility": 0.99 }
    },
    "segments": {
      "left_upper_arm": {
        "start": "left_shoulder",
        "end": "left_elbow",
        "start_point": { "x": 0.52, "y": 0.41, "z": -0.11, "visibility": 0.99 },
        "end_point": { "x": 0.57, "y": 0.53, "z": -0.09, "visibility": 0.97 }
      }
    }
  }
}
```

## Error Responses

If no pose has been produced yet:

Status: `503`

```json
{ "error": "No pose data yet" }
```

If wrong path is requested:

Status: `404`

```json
{ "error": "Not Found", "path": "/wrong" }
```

Health check:

Status: `200`

```json
{ "ok": true, "service": "holistic_tracker" }
```

## Landmark Keys

`pose.landmarks` includes exactly these keys:

- `nose`
- `left_eye_inner`
- `left_eye`
- `left_eye_outer`
- `right_eye_inner`
- `right_eye`
- `right_eye_outer`
- `left_ear`
- `right_ear`
- `mouth_left`
- `mouth_right`
- `left_shoulder`
- `right_shoulder`
- `left_elbow`
- `right_elbow`
- `left_wrist`
- `right_wrist`
- `left_pinky`
- `right_pinky`
- `left_index`
- `right_index`
- `left_thumb`
- `right_thumb`
- `left_hip`
- `right_hip`
- `left_knee`
- `right_knee`
- `left_ankle`
- `right_ankle`
- `left_heel`
- `right_heel`
- `left_foot_index`
- `right_foot_index`

Each landmark has this shape:

```json
{ "x": number, "y": number, "z": number, "visibility": number }
```

Notes:

- Values are rounded to 6 decimals.
- `x` and `y` are normalized image coordinates (typically in `[0,1]` when in frame).
- `z` is relative depth from MediaPipe.
- `visibility` is confidence-like in `[0,1]`.

## Segment Keys

`pose.segments` includes:

- `left_upper_arm`, `right_upper_arm`
- `left_forearm`, `right_forearm`
- `left_thigh`, `right_thigh`
- `left_calf`, `right_calf`
- `left_torso`, `right_torso`
- `shoulder_line`, `hip_line`

Each segment has this shape:

```json
{
  "start": "landmark_name",
  "end": "landmark_name",
  "start_point": { "x": number, "y": number, "z": number, "visibility": number },
  "end_point": { "x": number, "y": number, "z": number, "visibility": number }
}
```
