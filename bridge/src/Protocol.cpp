#include "Protocol.h"

#include <memory>
#include <sstream>

namespace moonray_bridge {

namespace {

struct TypeEntry {
    MessageType type;
    const char* name;
};

// Order matches MESSAGE_SCHEMA.md's "Message set" table.
constexpr TypeEntry kTypeTable[] = {
    {MessageType::HELLO, "HELLO"},
    {MessageType::CAPABILITIES, "CAPABILITIES"},
    {MessageType::CREATE_SCENE, "CREATE_SCENE"},
    {MessageType::UPDATE_OBJECT, "UPDATE_OBJECT"},
    {MessageType::UPDATE_CAMERA, "UPDATE_CAMERA"},
    {MessageType::UPDATE_MATERIAL, "UPDATE_MATERIAL"},
    {MessageType::START_RENDER, "START_RENDER"},
    {MessageType::STOP_RENDER, "STOP_RENDER"},
    {MessageType::FRAME_UPDATE, "FRAME_UPDATE"},
    {MessageType::RENDER_COMPLETE, "RENDER_COMPLETE"},
    {MessageType::ERROR, "ERROR"},
};

} // namespace

const char* messageTypeToString(MessageType type)
{
    for (const auto& entry : kTypeTable) {
        if (entry.type == type) return entry.name;
    }
    return "UNKNOWN";
}

MessageType messageTypeFromString(const std::string& s)
{
    for (const auto& entry : kTypeTable) {
        if (s == entry.name) return entry.type;
    }
    return MessageType::UNKNOWN;
}

bool decodeEnvelope(const std::string& jsonBody, Envelope* out, ErrorInfo* error)
{
    Json::CharReaderBuilder builder;
    std::unique_ptr<Json::CharReader> reader(builder.newCharReader());
    Json::Value root;
    std::string parseErrors;
    const char* begin = jsonBody.data();
    const char* end = begin + jsonBody.size();
    if (!reader->parse(begin, end, &root, &parseErrors)) {
        error->category = 1;
        error->code = "INVALID_JSON";
        error->message = "message body is not valid JSON: " + parseErrors;
        return false;
    }
    if (!root.isObject()) {
        error->category = 1;
        error->code = "INVALID_ENVELOPE";
        error->message = "envelope must be a JSON object";
        return false;
    }
    if (!root.isMember("protocol_version") || !root["protocol_version"].isInt()) {
        error->category = 1;
        error->code = "MISSING_PROTOCOL_VERSION";
        error->message = "envelope missing integer field 'protocol_version'";
        return false;
    }
    if (!root.isMember("type") || !root["type"].isString()) {
        error->category = 1;
        error->code = "MISSING_TYPE";
        error->message = "envelope missing string field 'type'";
        return false;
    }
    if (!root.isMember("id") || !root["id"].isString()) {
        error->category = 1;
        error->code = "MISSING_ID";
        error->message = "envelope missing string field 'id'";
        return false;
    }

    const std::string typeStr = root["type"].asString();
    const MessageType type = messageTypeFromString(typeStr);
    if (type == MessageType::UNKNOWN) {
        // MESSAGE_SCHEMA.md: "unknown message type -> hard ERROR, never silently ignore".
        error->category = 1;
        error->code = "UNKNOWN_MESSAGE_TYPE";
        error->message = "unrecognized message type: " + typeStr;
        return false;
    }

    out->protocolVersion = root["protocol_version"].asInt();
    out->type = type;
    out->id = root["id"].asString();
    out->payload = root.isMember("payload") ? root["payload"] : Json::Value(Json::objectValue);
    if (!out->payload.isObject()) {
        error->category = 1;
        error->code = "INVALID_PAYLOAD";
        error->message = "envelope field 'payload' must be a JSON object";
        return false;
    }
    return true;
}

std::string encodeEnvelope(const Envelope& env)
{
    Json::Value root(Json::objectValue);
    root["protocol_version"] = env.protocolVersion;
    root["type"] = messageTypeToString(env.type);
    root["id"] = env.id;
    root["payload"] = env.payload;

    Json::StreamWriterBuilder builder;
    builder["indentation"] = "";
    return Json::writeString(builder, root);
}

std::string encodeError(const std::string& id, const ErrorInfo& error)
{
    Envelope env;
    env.protocolVersion = kProtocolVersion;
    env.type = MessageType::ERROR;
    env.id = id;
    env.payload["category"] = error.category;
    env.payload["code"] = error.code;
    env.payload["message"] = error.message;
    return encodeEnvelope(env);
}

} // namespace moonray_bridge
