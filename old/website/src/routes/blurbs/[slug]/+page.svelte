<script>
  import showdown from "showdown";
  export let data;
  const rawHtml = new showdown.Converter({
    omitExtraWLInCodeBlocks: true,
    noHeaderId: false,
    parseImgDimensions: true,
    simplifiedAutoLink: true,
    literalMidWordUnderscores: true,
    strikethrough: true,
    tables: true,
    tablesHeaderId: false,
    ghCodeBlocks: true,
    tasklists: true,
    smoothLivePreview: true,
    disableForced4SpacesIndentedSublists: false,
    ghCompatibleHeaderId: true,
    smartIndentationFix: false,
    rawPrefixHeaderId: false,
    rawHeaderId: false,
    literalMidWordAsterisks: false,
    simpleLineBreaks: false,
    requireSpaceBeforeHeadingText: false,
    ghMentions: false,
    encodeEmails: true,
    openLinksInNewWindow: false,
    backslashEscapesHTMLTags: false,
    emoji: true,
    underline: true,
    ellipsis: true,
    completeHTMLDocument: false,
    metadata: false,
    splitAdjacentBlockquotes: false,
    moreStyling: true,
  }).makeHtml(data.content);
</script>

<div class="prose">
  <h1>{data.title}</h1>

  {@html rawHtml}
</div>

