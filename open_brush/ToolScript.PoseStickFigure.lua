Settings = {
    description = "Generates a one-shot stick figure from local pose API",
    space = "pointer",
    previewType = "sphere"
}

Parameters = {
    bodyWidth = {label = "Body Width", type = "float", min = 0.1, max = 4, default = 1.6},
    bodyHeight = {label = "Body Height", type = "float", min = 0.1, max = 4, default = 2.2},
    bodyDepth = {label = "Body Depth", type = "float", min = 0.1, max = 4, default = 1.2},
    minVisibility = {label = "Min Visibility", type = "float", min = 0, max = 1, default = 0.6}
}

local apiUrl = "http://127.0.0.1:40094/pose"
local poseData = nil
local requestInFlight = false
local pendingDraw = false

local function onPoseSuccess(result)
    requestInFlight = false

    local parsed = nil
    if type(result) == "string" then
        parsed = json.parse(result)
    elseif type(result) == "table" then
        parsed = result
    end

    if parsed and parsed.pose and parsed.pose.landmarks then
        poseData = parsed.pose
        pendingDraw = true
    end
end

local function onPoseError(_error)
    requestInFlight = false
    pendingDraw = false
end

local function requestPose()
    if requestInFlight then
        return
    end
    requestInFlight = true
    WebRequest:Get(apiUrl, onPoseSuccess, onPoseError)
end

local function hasVisibility(lm)
    return lm ~= nil and lm.visibility ~= nil and lm.visibility >= Parameters.minVisibility
end

local function toOffset(lm)
    local ox = (lm.x - 0.5) * Parameters.bodyWidth
    local oy = (0.5 - lm.y) * Parameters.bodyHeight
    local oz = (-lm.z) * Parameters.bodyDepth
    return Vector3:New(ox, oy, oz)
end

local function appendSegment(pathList, base, a, b)
    if not hasVisibility(a) or not hasVisibility(b) then
        return
    end

    local ao = toOffset(a)
    local bo = toOffset(b)
    local pa = Vector3:New(base.x + ao.x, base.y + ao.y, base.z + ao.z)
    local pb = Vector3:New(base.x + bo.x, base.y + bo.y, base.z + bo.z)

    local path = Path:New()
    path:Insert(Transform:New(pa, Rotation:New(0, 0, 0)))
    path:Insert(Transform:New(pb, Rotation:New(0, 0, 0)))
    pathList:Insert(path)
end

local function buildStickFigurePathList()
    if poseData == nil or poseData.landmarks == nil then
        return nil
    end

    local lm = poseData.landmarks
    local base = Symmetry.brushOffset
    local pathList = PathList:New()

    appendSegment(pathList, base, lm.left_shoulder, lm.right_shoulder)
    appendSegment(pathList, base, lm.left_hip, lm.right_hip)
    appendSegment(pathList, base, lm.left_shoulder, lm.left_hip)
    appendSegment(pathList, base, lm.right_shoulder, lm.right_hip)

    appendSegment(pathList, base, lm.left_shoulder, lm.left_elbow)
    appendSegment(pathList, base, lm.left_elbow, lm.left_wrist)
    appendSegment(pathList, base, lm.right_shoulder, lm.right_elbow)
    appendSegment(pathList, base, lm.right_elbow, lm.right_wrist)

    appendSegment(pathList, base, lm.left_hip, lm.left_knee)
    appendSegment(pathList, base, lm.left_knee, lm.left_ankle)
    appendSegment(pathList, base, lm.right_hip, lm.right_knee)
    appendSegment(pathList, base, lm.right_knee, lm.right_ankle)

    appendSegment(pathList, base, lm.nose, lm.left_shoulder)
    appendSegment(pathList, base, lm.nose, lm.right_shoulder)

    if pathList.count == 0 then
        return nil
    end
    pathList:Center()
    -- pathList:TranslateBy(Vector3:New(0, 1.5, 0))
    -- pathList:ScaleBy(10)
    return pathList
end

function Main()
    if Brush.triggerPressedThisFrame then
        requestPose()
    end

    if pendingDraw and Brush.triggerReleasedThisFrame then
        pendingDraw = false
        return buildStickFigurePathList()
    end
end
