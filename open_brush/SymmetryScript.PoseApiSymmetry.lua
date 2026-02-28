Settings = {
    description = "Pose-driven body-point symmetry using local AvatarStream API",
    space = "canvas",
}

Parameters = {
    pollEveryFrames = {label = "Poll Every Frames", type = "int", min = 1, max = 30, default = 6},
    bodyWidth = {label = "Body Width", type = "float", min = 0.1, max = 4, default = 1.6},
    bodyHeight = {label = "Body Height", type = "float", min = 0.1, max = 4, default = 2.2},
    bodyDepth = {label = "Body Depth", type = "float", min = 0.1, max = 4, default = 1.2},
    minVisibility = {label = "Min Visibility", type = "float", min = 0, max = 1, default = 0.45},
    debugEveryFrames = {label = "Debug Every Frames", type = "int", min = 0, max = 600, default = 60}
}

local apiUrl = "http://127.0.0.1:40094/pose"

local poseData = nil
local requestInFlight = false
local frameCounter = 0

local function onPoseSuccess(result)
    requestInFlight = false
    local parsed = nil
    if type(result) == "string" then
        parsed = json.parse(result)
    elseif type(result) == "table" then
        parsed = result
    else
        return
    end

    if parsed.pose and parsed.pose.landmarks then
        poseData = parsed.pose
    end
end

local function onPoseError(_error)
    requestInFlight = false
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

local function midpoint(a, b)
    return {
        x = (a.x + b.x) * 0.5,
        y = (a.y + b.y) * 0.5,
        z = (a.z + b.z) * 0.5,
        visibility = Math:Min(a.visibility, b.visibility)
    }
end


local function toOffset(lm)
    local ox = (lm.x - 0.5) * Parameters.bodyWidth
    local oy = (0.5 - lm.y) * Parameters.bodyHeight
    local oz = (-lm.z) * Parameters.bodyDepth
    return Vector3:New(ox, oy, oz)
end

local function insertPointer(pointers, base, lm)
    if not hasVisibility(lm) then
        return
    end
    local offset = toOffset(lm)
    local position = Vector3:New(base.x + offset.x, base.y + offset.y, base.z + offset.z)
    pointers:Insert(Transform:New(position, Rotation:New(0, 0, 0)))
end

local function addBodyPointers(pointers)
    if poseData == nil or poseData.landmarks == nil then
        return
    end

    local lm = poseData.landmarks
    local base = Symmetry.brushOffset
    insertPointer(pointers, base, lm.nose)
    insertPointer(pointers, base, lm.left_wrist)
    insertPointer(pointers, base, lm.right_wrist)
    insertPointer(pointers, base, lm.left_elbow)
    insertPointer(pointers, base, lm.right_elbow)
    insertPointer(pointers, base, lm.left_knee)
    insertPointer(pointers, base, lm.right_knee)
    insertPointer(pointers, base, lm.left_ankle)
    insertPointer(pointers, base, lm.right_ankle)

    if hasVisibility(lm.left_heel) and hasVisibility(lm.left_foot_index) then
        insertPointer(pointers, base, midpoint(lm.left_heel, lm.left_foot_index))
    end
    if hasVisibility(lm.right_heel) and hasVisibility(lm.right_foot_index) then
        insertPointer(pointers, base, midpoint(lm.right_heel, lm.right_foot_index))
    end

    if hasVisibility(lm.left_shoulder) and hasVisibility(lm.right_shoulder) then
        insertPointer(pointers, base, midpoint(lm.left_shoulder, lm.right_shoulder))
    end
    if hasVisibility(lm.left_hip) and hasVisibility(lm.right_hip) then
        insertPointer(pointers, base, midpoint(lm.left_hip, lm.right_hip))
    end
    if hasVisibility(lm.left_shoulder) and hasVisibility(lm.right_shoulder) and hasVisibility(lm.left_hip) and hasVisibility(lm.right_hip) then
        local chest = midpoint(lm.left_shoulder, lm.right_shoulder)
        local pelvis = midpoint(lm.left_hip, lm.right_hip)
        insertPointer(pointers, base, midpoint(chest, pelvis))
    end

    if hasVisibility(lm.left_shoulder) and hasVisibility(lm.left_elbow) then
        insertPointer(pointers, base, midpoint(lm.left_shoulder, lm.left_elbow))
    end
    if hasVisibility(lm.right_shoulder) and hasVisibility(lm.right_elbow) then
        insertPointer(pointers, base, midpoint(lm.right_shoulder, lm.right_elbow))
    end
    if hasVisibility(lm.left_elbow) and hasVisibility(lm.left_wrist) then
        insertPointer(pointers, base, midpoint(lm.left_elbow, lm.left_wrist))
    end
    if hasVisibility(lm.right_elbow) and hasVisibility(lm.right_wrist) then
        insertPointer(pointers, base, midpoint(lm.right_elbow, lm.right_wrist))
    end
    if hasVisibility(lm.left_hip) and hasVisibility(lm.left_knee) then
        insertPointer(pointers, base, midpoint(lm.left_hip, lm.left_knee))
    end
    if hasVisibility(lm.right_hip) and hasVisibility(lm.right_knee) then
        insertPointer(pointers, base, midpoint(lm.right_hip, lm.right_knee))
    end
    if hasVisibility(lm.left_knee) and hasVisibility(lm.left_ankle) then
        insertPointer(pointers, base, midpoint(lm.left_knee, lm.left_ankle))
    end
    if hasVisibility(lm.right_knee) and hasVisibility(lm.right_ankle) then
        insertPointer(pointers, base, midpoint(lm.right_knee, lm.right_ankle))
    end
end

function Start()
    requestPose()
end

function Main()
    frameCounter = frameCounter + 1
    if frameCounter % Parameters.pollEveryFrames == 0 then
        requestPose()
    end

    local pointers = Path:New()
    addBodyPointers(pointers)

    if Parameters.debugEveryFrames > 0 and frameCounter % Parameters.debugEveryFrames == 0 then
        --
    end
    
    pointers:Center()
    -- print("before: " .. pointers[0].position.x)
    pointers:TranslateBy(Vector3.up * 0.5)
    pointers:ScaleBy(Vector3.one * 5)
    -- print("after: " .. pointers[0].position.x)
    -- print("-----------------")
    return pointers
end


