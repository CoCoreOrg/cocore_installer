import json
DEMARCATION = "-=-=-=-=-=-=-=-=-=-=-"
class TaskExtensions:
    @classmethod
    def python_extension(cls, args):
        arg_data = json.dumps(args)
        return f"""
if __name__ == '__main__':
    import json
    json_string = \"\"\"{arg_data}\"\"\"
    json_string = json_string.replace("\\n", "\\\\n")
    args = json.loads(json_string)
    result = run(*args)
    print("{DEMARCATION}")
    print(json.dumps(result))
"""

    @classmethod
    def node_extension(cls, args):
        return f"""
const args = JSON.parse('{json.dumps(args)}');
const result = run(...args);
console.log("{DEMARCATION}");
console.log(JSON.stringify(result, null, 2));
"""

    @classmethod
    def ruby_extension(cls, args):
        return f"""
require 'json'
args = JSON.parse('{args}')
result = run(*args)
puts "{DEMARCATION}"
puts JSON.pretty_generate(result)
"""

    @classmethod
    def go_extension(cls, args):
        return f"""
func main() {{
    var args []interface{{}}
    err := json.Unmarshal([]byte(`{json.dumps(args)}`), &args)
    if err != nil {{
        fmt.Println("Error:", err)
        os.Exit(1)
    }}

    result := run(args)
    jsonResult, err := json.MarshalIndent(result, "", "  ")
    if err != nil {{
        fmt.Println("Error serializing result:", err)
        os.Exit(1)
    }}

    fmt.Println("{DEMARCATION}")
    fmt.Println(string(jsonResult))
}}
"""

    @classmethod
    def rust_extension(cls, args):
        return f"""
use serde_json::{{Value, to_string_pretty}};

fn main() {{
    let args: Value = serde_json::from_str("{args}").unwrap();

    if let Value::Array(vec) = args {{
        let result = run(vec);  // Pass the args directly to the run function provided in task_code
        let json_result = to_string_pretty(&result).unwrap();
        println!("{DEMARCATION}");
        println!("{{}}", json_result);  // Print the JSON string of the result
    }} else {{
        println!("Error: Arguments should be a JSON array");
    }}
}}
"""

    @classmethod
    def java_extension(cls, args):
        args_json = json.dumps(args)
        return f"""
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Iterator;

public class TaskCode {{
    public static void main(String[] args) {{
        try {{
            ObjectMapper mapper = new ObjectMapper();
            JsonNode rootNode = mapper.readTree("{args_json}");
            JsonNode[] inputs = new JsonNode[rootNode.size()];
            int index = 0;
            for (Iterator<JsonNode> it = rootNode.elements(); it.hasNext(); index++) {{
                inputs[index] = it.next();
            }}
            JsonNode result = run(inputs);
            System.out.println("{DEMARCATION}");
            System.out.println(mapper.writerWithDefaultPrettyPrinter().writeValueAsString(result));
        }} catch (Exception e) {{
            e.printStackTrace();
        }}
    }}

    /*METHOD_PLACEHOLDER*/
}}
"""