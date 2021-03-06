<div class='tag-list'>
    <% if (ctx.results.length) { %>
        <table>
            <thead>
                <th class='names'>
                    <% if (ctx.query == 'sort:name' || !ctx.query) { %>
                        <a href='/tags/text=-sort:name'>Tag name(s)</a>
                    <% } else { %>
                        <a href='/tags/text=sort:name'>Tag name(s)</a>
                    <% } %>
                </th>
                <th class='implications'>
                    <% if (ctx.query == 'sort:implication-count') { %>
                        <a href='/tags/text=-sort:implication-count'>Implications</a>
                    <% } else { %>
                        <a href='/tags/text=sort:implication-count'>Implications</a>
                    <% } %>
                </th>
                <th class='suggestions'>
                    <% if (ctx.query == 'sort:suggestion-count') { %>
                        <a href='/tags/text=-sort:suggestion-count'>Suggestions</a>
                    <% } else { %>
                        <a href='/tags/text=sort:suggestion-count'>Suggestions</a>
                    <% } %>
                </th>
                <th class='usages'>
                    <% if (ctx.query == 'sort:usages') { %>
                        <a href='/tags/text=-sort:usages'>Usages</a>
                    <% } else { %>
                        <a href='/tags/text=sort:usages'>Usages</a>
                    <% } %>
                </th>
            </thead>
            <tbody>
                <% _.each(ctx.results, tag => { %>
                    <tr>
                        <td class='names'>
                            <ul>
                                <% _.each(tag.names, name => { %>
                                    <li><%= ctx.makeTagLink(name) %></li>
                                <% }) %>
                            </ul>
                        </td>
                        <td class='implications'>
                            <% if (tag.implications.length) { %>
                                <ul>
                                    <% _.each(tag.implications, name => { %>
                                        <li><%= ctx.makeTagLink(name) %></li>
                                    <% }) %>
                                </ul>
                            <% } else { %>
                                -
                            <% } %>
                        </td>
                        <td class='suggestions'>
                            <% if (tag.suggestions.length) { %>
                                <ul>
                                    <% _.each(tag.suggestions, name => { %>
                                        <li><%= ctx.makeTagLink(name) %></li>
                                    <% }) %>
                                </ul>
                            <% } else { %>
                                -
                            <% } %>
                        </td>
                        <td class='usages'>
                            <%= tag.usages %>
                        </td>
                    </tr>
                <% }) %>
            </tbody>
        </table>
    <% } %>
</div>
