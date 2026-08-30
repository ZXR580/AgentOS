import {
  db,
  getStyles,
  renderer
} from "./chunk-4TTKWINT.js";
import {
  populateCommonDb
} from "./chunk-7ST5RZJI.js";
import {
  MermaidParseError
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
import {
  createRailroadAbnfServices
} from "./chunk-5OCEKQLU.js";
import "./chunk-XO65CYX7.js";
import "./chunk-RBLF6UOP.js";
import "./chunk-NHWGI6CF.js";
import "./chunk-LHPUQNBD.js";
import "./chunk-VYGLIPR4.js";
import "./chunk-6IZFD337.js";
import "./chunk-QEOULI6B.js";
import "./chunk-ERNGLA6Z.js";
import {
  log
} from "./chunk-6UOEWA3S.js";
import {
  __name
} from "./chunk-DTCXZATX.js";
import "./chunk-DC5AMYBS.js";

// node_modules/mermaid/dist/chunks/mermaid.core/abnfDiagram-VCTEODGH.mjs
var langiumParser = createRailroadAbnfServices().RailroadAbnf.parser.LangiumParser;
var transformAlternation = __name((alt) => {
  const alternatives = alt.alternatives.map(transformConcatenation);
  if (alternatives.length === 1) {
    return alternatives[0];
  }
  return {
    type: "choice",
    alternatives
  };
}, "transformAlternation");
var transformConcatenation = __name((concat) => {
  const elements = concat.elements.map(transformElement);
  if (elements.length === 1) {
    return elements[0];
  }
  return {
    type: "sequence",
    elements
  };
}, "transformConcatenation");
var parseRepeat = __name((repeat) => {
  if (repeat.includes("*")) {
    const [minStr, maxStr] = repeat.split("*");
    const min = minStr ? parseInt(minStr, 10) : 0;
    const max = maxStr ? parseInt(maxStr, 10) : Infinity;
    return { min, max };
  }
  const exact = parseInt(repeat, 10);
  return { min: exact, max: exact };
}, "parseRepeat");
var transformElement = __name((element) => {
  const inner = transformPrimary(element.primary);
  if (!element.repeat) {
    return inner;
  }
  const { min, max } = parseRepeat(element.repeat);
  if (min === 0 && max === 1) {
    return { type: "optional", element: inner };
  }
  return {
    type: "repetition",
    element: inner,
    min,
    max
  };
}, "transformElement");
var transformPrimary = __name((primary) => {
  switch (primary.$type) {
    case "AbnfStringLiteral":
      return {
        type: "terminal",
        value: primary.value
      };
    case "AbnfNumVal":
      return {
        type: "terminal",
        value: primary.value
      };
    case "AbnfRuleName":
      return {
        type: "nonterminal",
        name: primary.name
      };
    case "AbnfGroup":
      return transformAlternation(primary.element);
    case "AbnfOptionalGroup":
      return {
        type: "optional",
        element: transformAlternation(primary.element)
      };
    default:
      throw new Error(`Unsupported ABNF primary node: ${primary.$type}`);
  }
}, "transformPrimary");
var transformRule = __name((rule) => {
  return {
    name: rule.name,
    definition: transformAlternation(rule.definition)
  };
}, "transformRule");
var populateDb = __name((ast) => {
  populateCommonDb(ast, db);
  if (ast.title) {
    db.setTitle(ast.title);
  }
  ast.rules.map((rule) => db.addRule(transformRule(rule)));
}, "populateDb");
var parser = {
  parse: __name((input) => {
    db.clear();
    log.debug("[ABNF Parser] Starting Langium parse");
    const result = langiumParser.parse(input);
    if (result.lexerErrors.length > 0 || result.parserErrors.length > 0) {
      throw new MermaidParseError(result);
    }
    const ast = result.value;
    log.debug("[ABNF Parser] Parsed rules:", ast.rules.length);
    populateDb(ast);
    log.debug("[ABNF Parser] Parse complete");
  }, "parse"),
  parser: {
    yy: db
  }
};
var diagram = {
  parser,
  db,
  renderer,
  styles: getStyles
};
export {
  diagram
};
//# sourceMappingURL=abnfDiagram-VCTEODGH-2MPO4H6C.js.map
