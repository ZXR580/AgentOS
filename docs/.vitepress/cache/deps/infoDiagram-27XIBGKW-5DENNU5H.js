import {
  parse
} from "./chunk-ILVLSLDG.js";
import "./chunk-JJL23HVX.js";
import "./chunk-JIBVRVNW.js";
import "./chunk-BESAVCCD.js";
import "./chunk-OLOE3V3X.js";
import "./chunk-3W4J5PDF.js";
import "./chunk-RR6R2DPB.js";
import "./chunk-YKP6VMVM.js";
import "./chunk-MEJO2UIF.js";
import "./chunk-7WXCNXZT.js";
import "./chunk-5OCEKQLU.js";
import "./chunk-XO65CYX7.js";
import "./chunk-RBLF6UOP.js";
import "./chunk-NHWGI6CF.js";
import "./chunk-LHPUQNBD.js";
import "./chunk-VYGLIPR4.js";
import "./chunk-6IZFD337.js";
import {
  selectSvgElement
} from "./chunk-QEOULI6B.js";
import {
  configureSvgSize
} from "./chunk-ERNGLA6Z.js";
import {
  log
} from "./chunk-6UOEWA3S.js";
import {
  __name
} from "./chunk-DTCXZATX.js";
import "./chunk-DC5AMYBS.js";

// node_modules/mermaid/dist/chunks/mermaid.core/infoDiagram-27XIBGKW.mjs
var parser = {
  parse: __name(async (input) => {
    const ast = await parse("info", input);
    log.debug(ast);
  }, "parse")
};
var DEFAULT_INFO_DB = {
  version: "11.17.2" + (true ? "" : "-tiny")
};
var getVersion = __name(() => DEFAULT_INFO_DB.version, "getVersion");
var db = {
  getVersion
};
var draw = __name((text, id, version) => {
  log.debug("rendering info diagram\n" + text);
  const svg = selectSvgElement(id);
  configureSvgSize(svg, 100, 400, true);
  const group = svg.append("g");
  group.append("text").attr("x", 100).attr("y", 40).attr("class", "version").attr("font-size", 32).style("text-anchor", "middle").text(`v${version}`);
}, "draw");
var renderer = { draw };
var diagram = {
  parser,
  db,
  renderer
};
export {
  diagram
};
//# sourceMappingURL=infoDiagram-27XIBGKW-5DENNU5H.js.map
